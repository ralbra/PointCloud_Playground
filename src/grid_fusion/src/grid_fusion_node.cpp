#include <algorithm>
#include <chrono>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "builtin_interfaces/msg/time.hpp"
#include "grid_map_msgs/msg/grid_map.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "rcl_interfaces/msg/parameter_descriptor.hpp"
#include "rcl_interfaces/msg/set_parameters_result.hpp"
#include "rclcpp/rclcpp.hpp"

#include "grid_fusion/fusion.hpp"

namespace gf = grid_fusion;

namespace
{
enum class Quantity
{
  Intensity,
  Height
};

enum class Kind
{
  Occupancy,
  GridMap
};

// One fused output: a quantity (intensity or height) in one message type.
struct Channel
{
  Quantity quantity = Quantity::Intensity;
  Kind kind = Kind::Occupancy;
  std::string label;
  std::vector<gf::GridSnapshot> inputs;  // one per configured input
  std::vector<gf::InputState> previous;  // only used to log state changes
  std::vector<rclcpp::SubscriptionBase::SharedPtr> subscriptions;
  rclcpp::Publisher<nav_msgs::msg::OccupancyGrid>::SharedPtr occupancy_pub;
  rclcpp::Publisher<grid_map_msgs::msg::GridMap>::SharedPtr grid_map_pub;
};
}  // namespace

class GridFusion : public rclcpp::Node
{
public:
  GridFusion()
  : Node("grid_fusion_node")
  {
    // startup-only parameters (read-only at runtime)
    prefixes_ = readOnlyParameter<std::vector<std::string>>("inputs", {});
    output_prefix_ = readOnlyParameter<std::string>("output_prefix", "fused");
    const std::string intensity_topic =
      readOnlyParameter<std::string>("intensity_topic", "intensity_grid");
    const std::string height_topic = readOnlyParameter<std::string>("height_topic", "height_grid");
    const std::string intensity_map_topic =
      readOnlyParameter<std::string>("intensity_gridmap_topic", "intensity_gridmap");
    const std::string height_map_topic =
      readOnlyParameter<std::string>("height_gridmap_topic", "height_gridmap");
    const bool fuse_grids = readOnlyParameter<bool>("fuse_occupancy_grids", true);
    const bool fuse_maps = readOnlyParameter<bool>("fuse_grid_maps", true);
    const double rate = readOnlyParameter<double>("publish_rate", 10.0);

    // parameters that can change at runtime
    this->declare_parameter<std::string>("intensity_rule", "mean");
    this->declare_parameter<std::string>("height_rule", "max");
    this->declare_parameter<double>("input_timeout", 1.0);
    this->declare_parameter<int64_t>("min_fresh_inputs", 1);

    std::string intensity_rule_name;
    std::string height_rule_name;
    int64_t min_inputs = 1;
    this->get_parameter("intensity_rule", intensity_rule_name);
    this->get_parameter("height_rule", height_rule_name);
    this->get_parameter("input_timeout", timeout_s_);
    this->get_parameter("min_fresh_inputs", min_inputs);

    if (prefixes_.empty()) {
      throw std::invalid_argument("parameter 'inputs' is empty: list at least one grid prefix");
    }
    if (!fuse_grids && !fuse_maps) {
      throw std::invalid_argument("fuse_occupancy_grids and fuse_grid_maps are both false");
    }
    if (!gf::parseFusionRule(intensity_rule_name, intensity_rule_) ||
      !gf::parseFusionRule(height_rule_name, height_rule_))
    {
      throw std::invalid_argument(
              "intensity_rule and height_rule must be one of: max, min, sum, mean, latest");
    }
    if (rate <= 0.0 || timeout_s_ <= 0.0) {
      throw std::invalid_argument("publish_rate and input_timeout must be > 0");
    }
    if (min_inputs < 1 || min_inputs > static_cast<int64_t>(prefixes_.size())) {
      throw std::invalid_argument("min_fresh_inputs must be between 1 and the number of inputs");
    }
    min_inputs_ = static_cast<size_t>(min_inputs);
    timeout_ns_ = static_cast<int64_t>(timeout_s_ * 1e9);

    if (fuse_grids) {
      addChannel(Quantity::Intensity, Kind::Occupancy, intensity_topic);
      addChannel(Quantity::Height, Kind::Occupancy, height_topic);
    }
    if (fuse_maps) {
      addChannel(Quantity::Intensity, Kind::GridMap, intensity_map_topic);
      addChannel(Quantity::Height, Kind::GridMap, height_map_topic);
    }

    timer_ = this->create_wall_timer(
      std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::duration<double>(1.0 / rate)),
      [this]() {fuseAndPublish();});
    callback_handle_ = this->add_on_set_parameters_callback(
      [this](const std::vector<rclcpp::Parameter> & p) {return onParameters(p);});

    RCLCPP_INFO(
      get_logger(),
      "Fusing %zu inputs at %.1f Hz: intensity rule '%s', height rule '%s', "
      "timeout %.2f s, min fresh inputs %zu",
      prefixes_.size(), rate, gf::fusionRuleName(intensity_rule_),
      gf::fusionRuleName(height_rule_), timeout_s_, min_inputs_);
  }

private:
  template<typename T>
  T readOnlyParameter(const std::string & name, const T & default_value)
  {
    rcl_interfaces::msg::ParameterDescriptor descriptor;
    descriptor.read_only = true;
    this->declare_parameter<T>(name, default_value, descriptor);
    T value{};
    this->get_parameter(name, value);
    return value;
  }

  void addChannel(Quantity quantity, Kind kind, const std::string & suffix)
  {
    Channel channel;
    channel.quantity = quantity;
    channel.kind = kind;
    channel.label = std::string(quantity == Quantity::Intensity ? "intensity" : "height") +
      (kind == Kind::Occupancy ? " grid" : " gridmap");
    channel.inputs.resize(prefixes_.size());
    channel.previous.assign(prefixes_.size(), gf::InputState::kNoData);

    const size_t index = channels_.size();
    // best effort connects to both reliable and best-effort publishers
    const auto qos = rclcpp::QoS(5).reliability(RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT);

    for (size_t i = 0; i < prefixes_.size(); ++i) {
      const std::string topic = gf::joinTopic(prefixes_[i], suffix);
      if (kind == Kind::Occupancy) {
        channel.subscriptions.push_back(
          this->create_subscription<nav_msgs::msg::OccupancyGrid>(
            topic, qos, [this, index, i](nav_msgs::msg::OccupancyGrid::ConstSharedPtr msg) {
              store(index, i, gf::snapshotOf(std::move(msg), this->now().nanoseconds()));
            }));
      } else {
        channel.subscriptions.push_back(
          this->create_subscription<grid_map_msgs::msg::GridMap>(
            topic, qos, [this, index, i](grid_map_msgs::msg::GridMap::ConstSharedPtr msg) {
              store(index, i, gf::snapshotOf(std::move(msg), this->now().nanoseconds()));
            }));
      }
      RCLCPP_INFO(get_logger(), "Subscribing to %s", topic.c_str());
    }

    const std::string out_topic = gf::joinTopic(output_prefix_, suffix);
    if (kind == Kind::Occupancy) {
      channel.occupancy_pub = this->create_publisher<nav_msgs::msg::OccupancyGrid>(out_topic, 10);
    } else {
      channel.grid_map_pub = this->create_publisher<grid_map_msgs::msg::GridMap>(out_topic, 10);
    }
    RCLCPP_INFO(
      get_logger(), "Publishing fused %s to %s", channel.label.c_str(),
      out_topic.c_str());
    channels_.push_back(std::move(channel));
  }

  void store(size_t channel, size_t input, gf::GridSnapshot snapshot)
  {
    if (snapshot.cells.empty()) {
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 5000,
        "Ignoring an empty or inconsistent %s from '%s'",
        channels_[channel].label.c_str(), prefixes_[input].c_str());
      return;
    }
    channels_[channel].inputs[input] = std::move(snapshot);
  }

  void fuseAndPublish()
  {
    const int64_t now_ns = this->now().nanoseconds();
    for (auto & channel : channels_) {
      publishChannel(channel, now_ns);
    }
  }

  void publishChannel(Channel & channel, int64_t now_ns)
  {
    const gf::FusionRule rule =
      channel.quantity == Quantity::Intensity ? intensity_rule_ : height_rule_;
    const gf::FusionResult result =
      gf::fuseSnapshots(channel.inputs, rule, now_ns, timeout_ns_, min_inputs_);
    logTransitions(channel, result);

    if (result.cells.empty()) {
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 5000,
        "%s: %zu of %zu inputs usable (need %zu), not publishing",
        channel.label.c_str(), result.used, prefixes_.size(), min_inputs_);
      return;
    }

    const gf::GridSnapshot & reference = channel.inputs[static_cast<size_t>(result.reference)];
    const builtin_interfaces::msg::Time stamp = this->now();

    if (channel.kind == Kind::Occupancy) {
      nav_msgs::msg::OccupancyGrid out = *reference.occupancy;
      gf::fillOccupancyGrid(out, result.cells, reference.frame_id, stamp);
      channel.occupancy_pub->publish(out);
    } else {
      grid_map_msgs::msg::GridMap out = *reference.grid_map;
      if (!gf::fillGridMap(out, result.cells, reference.frame_id, stamp)) {
        RCLCPP_WARN_THROTTLE(
          get_logger(), *get_clock(), 5000,
          "%s: layer size does not match the fused cells, not publishing",
          channel.label.c_str());
        return;
      }
      channel.grid_map_pub->publish(out);
    }
  }

  // Logs only when an input changes state, so a stalled source warns once.
  void logTransitions(Channel & channel, const gf::FusionResult & result)
  {
    for (size_t i = 0; i < result.states.size(); ++i) {
      const gf::InputState state = result.states[i];
      if (state == channel.previous[i]) {
        continue;
      }
      channel.previous[i] = state;

      switch (state) {
        case gf::InputState::kStale:
          RCLCPP_WARN(
            get_logger(),
            "Input '%s' (%s): no new grid for more than %.2f s, excluded until it recovers",
            prefixes_[i].c_str(), channel.label.c_str(), timeout_s_);
          break;
        case gf::InputState::kIncompatible:
          RCLCPP_WARN(
            get_logger(),
            "Input '%s' (%s): frame or geometry differs from reference input '%s', excluded",
            prefixes_[i].c_str(), channel.label.c_str(),
            prefixes_[static_cast<size_t>(result.reference)].c_str());
          break;
        case gf::InputState::kUsed:
          RCLCPP_INFO(
            get_logger(), "Input '%s' (%s): contributing", prefixes_[i].c_str(),
            channel.label.c_str());
          break;
        case gf::InputState::kNoData:
          break;
      }
    }
  }

  rcl_interfaces::msg::SetParametersResult onParameters(
    const std::vector<rclcpp::Parameter> & parameters)
  {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true;

    gf::FusionRule intensity_rule = intensity_rule_;
    gf::FusionRule height_rule = height_rule_;
    double timeout_s = timeout_s_;
    size_t min_inputs = min_inputs_;

    // validate everything first so a bad value changes nothing
    for (const auto & p : parameters) {
      const std::string & name = p.get_name();
      if (name == "intensity_rule" || name == "height_rule") {
        gf::FusionRule rule = gf::FusionRule::Max;
        if (!gf::parseFusionRule(p.as_string(), rule)) {
          result.successful = false;
          result.reason = name + " must be one of: max, min, sum, mean, latest";
          return result;
        }
        (name == "intensity_rule" ? intensity_rule : height_rule) = rule;
      } else if (name == "input_timeout") {
        if (p.as_double() <= 0.0) {
          result.successful = false;
          result.reason = "input_timeout must be > 0";
          return result;
        }
        timeout_s = p.as_double();
      } else if (name == "min_fresh_inputs") {
        const int64_t v = p.as_int();
        if (v < 1 || v > static_cast<int64_t>(prefixes_.size())) {
          result.successful = false;
          result.reason = "min_fresh_inputs must be between 1 and the number of inputs";
          return result;
        }
        min_inputs = static_cast<size_t>(v);
      }
    }

    intensity_rule_ = intensity_rule;
    height_rule_ = height_rule;
    timeout_s_ = timeout_s;
    timeout_ns_ = static_cast<int64_t>(timeout_s * 1e9);
    min_inputs_ = min_inputs;
    RCLCPP_INFO(
      get_logger(), "Updated: intensity rule '%s', height rule '%s', timeout %.2f s, min fresh inputs %zu",
      gf::fusionRuleName(intensity_rule_), gf::fusionRuleName(height_rule_), timeout_s_,
      min_inputs_);
    return result;
  }

  std::vector<std::string> prefixes_;
  std::string output_prefix_;
  gf::FusionRule intensity_rule_ = gf::FusionRule::Mean;
  gf::FusionRule height_rule_ = gf::FusionRule::Max;
  double timeout_s_ = 1.0;
  int64_t timeout_ns_ = 1000000000LL;
  size_t min_inputs_ = 1;

  std::vector<Channel> channels_;
  rclcpp::TimerBase::SharedPtr timer_;
  OnSetParametersCallbackHandle::SharedPtr callback_handle_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  int exit_code = 0;
  try {
    rclcpp::spin(std::make_shared<GridFusion>());
  } catch (const std::exception & e) {
    RCLCPP_FATAL(rclcpp::get_logger("grid_fusion_node"), "%s", e.what());
    exit_code = 1;
  }
  rclcpp::shutdown();
  return exit_code;
}
