#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "builtin_interfaces/msg/time.hpp"
#include "grid_map_msgs/msg/grid_map.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"

namespace grid_fusion
{

// Cell value meaning "no information". Known cells stay within [-127, 127].
inline constexpr signed char kUnknownCell = -128;
inline constexpr int64_t kNever = std::numeric_limits<int64_t>::min();

// ---------- topics ----------
// "front" + "intensity_grid" -> "front/intensity_grid"; an empty prefix gives the bare name.
inline std::string joinTopic(std::string prefix, const std::string & name)
{
  if (prefix.empty()) {
    return name;
  }
  while (!prefix.empty() && prefix.back() == '/') {
    prefix.pop_back();
  }
  return prefix + "/" + name;
}

// ---------- combine rules ----------
enum class FusionRule
{
  Max,
  Min,
  Sum,
  Mean,
  Latest
};

inline bool parseFusionRule(const std::string & name, FusionRule & rule)
{
  if (name == "max") {rule = FusionRule::Max; return true;}
  if (name == "min") {rule = FusionRule::Min; return true;}
  if (name == "sum") {rule = FusionRule::Sum; return true;}
  if (name == "mean") {rule = FusionRule::Mean; return true;}
  if (name == "latest") {rule = FusionRule::Latest; return true;}
  return false;
}

inline const char * fusionRuleName(FusionRule rule)
{
  switch (rule) {
    case FusionRule::Max: return "max";
    case FusionRule::Min: return "min";
    case FusionRule::Sum: return "sum";
    case FusionRule::Mean: return "mean";
    case FusionRule::Latest: return "latest";
  }
  return "";
}

// Combines layers cell by cell. Unknown cells are ignored; a cell that is
// unknown in every layer stays unknown. Layers must be ordered oldest to
// newest (only "latest" cares) and have the same size.
inline std::vector<signed char> fuseLayers(
  FusionRule rule, const std::vector<const std::vector<signed char> *> & layers)
{
  if (layers.empty()) {
    return {};
  }
  const size_t n = layers.front()->size();
  std::vector<signed char> out(n, kUnknownCell);

  for (size_t i = 0; i < n; ++i) {
    int count = 0;
    int sum = 0;
    int max_v = std::numeric_limits<int>::min();
    int min_v = std::numeric_limits<int>::max();
    int latest = kUnknownCell;

    for (const auto * layer : layers) {
      if (i >= layer->size()) {
        continue;
      }
      const int v = (*layer)[i];
      if (v == kUnknownCell) {
        continue;
      }
      ++count;
      sum += v;
      max_v = std::max(max_v, v);
      min_v = std::min(min_v, v);
      latest = v;
    }
    if (count == 0) {
      continue;
    }

    int result = 0;
    switch (rule) {
      case FusionRule::Max: result = max_v; break;
      case FusionRule::Min: result = min_v; break;
      case FusionRule::Sum: result = sum; break;
      case FusionRule::Mean:
        result = static_cast<int>(std::lround(static_cast<double>(sum) / count));
        break;
      case FusionRule::Latest: result = latest; break;
    }
    // -128 is reserved for "unknown", so a known cell never leaves [-127, 127]
    out[i] = static_cast<signed char>(std::clamp(result, -127, 127));
  }
  return out;
}

// ---------- geometry ----------
struct GridGeometry
{
  double resolution = 0.0;
  double length_x = 0.0;
  double length_y = 0.0;
  double pos_x = 0.0;
  double pos_y = 0.0;
  double pos_z = 0.0;
  double ori_x = 0.0;
  double ori_y = 0.0;
  double ori_z = 0.0;
  double ori_w = 1.0;
  size_t cell_count = 0;
};

inline GridGeometry geometryOf(const nav_msgs::msg::OccupancyGrid & g)
{
  GridGeometry r;
  r.resolution = g.info.resolution;
  r.length_x = static_cast<double>(g.info.width) * static_cast<double>(g.info.resolution);
  r.length_y = static_cast<double>(g.info.height) * static_cast<double>(g.info.resolution);
  r.pos_x = g.info.origin.position.x;
  r.pos_y = g.info.origin.position.y;
  r.pos_z = g.info.origin.position.z;
  r.ori_x = g.info.origin.orientation.x;
  r.ori_y = g.info.origin.orientation.y;
  r.ori_z = g.info.origin.orientation.z;
  r.ori_w = g.info.origin.orientation.w;
  r.cell_count = g.data.size();
  return r;
}

inline GridGeometry geometryOf(const grid_map_msgs::msg::GridMap & g)
{
  GridGeometry r;
  r.resolution = g.info.resolution;
  r.length_x = g.info.length_x;
  r.length_y = g.info.length_y;
  r.pos_x = g.info.pose.position.x;
  r.pos_y = g.info.pose.position.y;
  r.pos_z = g.info.pose.position.z;
  r.ori_x = g.info.pose.orientation.x;
  r.ori_y = g.info.pose.orientation.y;
  r.ori_z = g.info.pose.orientation.z;
  r.ori_w = g.info.pose.orientation.w;
  r.cell_count = g.data.empty() ? 0 : g.data[0].data.size();
  return r;
}

inline bool sameGeometry(const GridGeometry & a, const GridGeometry & b, double tol = 1e-6)
{
  const auto near = [tol](double x, double y) {return std::abs(x - y) <= tol;};
  return a.cell_count == b.cell_count && near(a.resolution, b.resolution) &&
         near(a.length_x, b.length_x) && near(a.length_y, b.length_y) &&
         near(a.pos_x, b.pos_x) && near(a.pos_y, b.pos_y) && near(a.pos_z, b.pos_z) &&
         near(a.ori_x, b.ori_x) && near(a.ori_y, b.ori_y) && near(a.ori_z, b.ori_z) &&
         near(a.ori_w, b.ori_w);
}

// ---------- message conversion ----------
// GridMap layers hold cells / 127 (see fillGridMap); this is the inverse.
inline signed char gridMapValueToCell(float value)
{
  if (!std::isfinite(value)) {
    return kUnknownCell;
  }
  const long cell = std::lround(value * 127.0f);
  return static_cast<signed char>(std::clamp(cell, -128L, 127L));
}

// Uses the first layer, which is the only one a pointcloud_to_grid node publishes.
inline std::vector<signed char> cellsOf(const grid_map_msgs::msg::GridMap & g)
{
  std::vector<signed char> cells;
  if (g.data.empty()) {
    return cells;
  }
  cells.reserve(g.data[0].data.size());
  for (const float v : g.data[0].data) {
    cells.push_back(gridMapValueToCell(v));
  }
  return cells;
}

inline void fillOccupancyGrid(
  nav_msgs::msg::OccupancyGrid & grid,
  const std::vector<signed char> & cells,
  const std::string & frame_id,
  const builtin_interfaces::msg::Time & stamp)
{
  grid.header.stamp = stamp;
  grid.header.frame_id = frame_id;
  grid.info.map_load_time = stamp;
  grid.data = cells;
}

// The layer must already be sized. Returns false, and leaves the data
// untouched, if the sizes do not match.
inline bool fillGridMap(
  grid_map_msgs::msg::GridMap & msg,
  const std::vector<signed char> & cells,
  const std::string & frame_id,
  const builtin_interfaces::msg::Time & stamp)
{
  msg.header.stamp = stamp;
  msg.header.frame_id = frame_id;
  if (msg.data.empty() || msg.data[0].data.size() != cells.size()) {
    return false;
  }
  for (size_t i = 0; i < cells.size(); ++i) {
    msg.data[0].data[i] = static_cast<float>(cells[i]) / 127.0f;
  }
  return true;
}

// ---------- last received grid of one input ----------
struct GridSnapshot
{
  int64_t received_ns = kNever;
  std::string frame_id;
  GridGeometry geometry;
  std::vector<signed char> cells;                          // empty = unusable
  nav_msgs::msg::OccupancyGrid::ConstSharedPtr occupancy;  // set for OccupancyGrid inputs
  grid_map_msgs::msg::GridMap::ConstSharedPtr grid_map;    // set for GridMap inputs
};

inline GridSnapshot snapshotOf(
  nav_msgs::msg::OccupancyGrid::ConstSharedPtr msg,
  int64_t received_ns)
{
  GridSnapshot s;
  s.received_ns = received_ns;
  s.frame_id = msg->header.frame_id;
  s.geometry = geometryOf(*msg);
  const size_t expected =
    static_cast<size_t>(msg->info.width) * static_cast<size_t>(msg->info.height);
  if (expected == msg->data.size()) {
    s.cells = msg->data;
  }
  s.occupancy = std::move(msg);
  return s;
}

inline GridSnapshot snapshotOf(grid_map_msgs::msg::GridMap::ConstSharedPtr msg, int64_t received_ns)
{
  GridSnapshot s;
  s.received_ns = received_ns;
  s.frame_id = msg->header.frame_id;
  s.geometry = geometryOf(*msg);
  s.cells = cellsOf(*msg);
  s.grid_map = std::move(msg);
  return s;
}

// ---------- fusing the inputs ----------
enum class InputState
{
  kNoData,        // nothing received yet
  kStale,         // older than the timeout (or stamped in the future)
  kIncompatible,  // frame or geometry differs from the reference input
  kUsed
};

struct FusionResult
{
  std::vector<signed char> cells;  // empty if fewer than min_inputs inputs were usable
  int reference = -1;              // input that defines frame and geometry, -1 if none
  size_t used = 0;
  std::vector<InputState> states;  // one per input, same order
};

inline FusionResult fuseSnapshots(
  const std::vector<GridSnapshot> & inputs, FusionRule rule,
  int64_t now_ns, int64_t timeout_ns, size_t min_inputs)
{
  FusionResult result;
  result.states.assign(inputs.size(), InputState::kNoData);

  std::vector<size_t> fresh;
  for (size_t i = 0; i < inputs.size(); ++i) {
    const GridSnapshot & in = inputs[i];
    if (in.received_ns == kNever || in.cells.empty()) {
      continue;
    }
    const int64_t age_ns = now_ns - in.received_ns;
    if (age_ns < 0 || age_ns > timeout_ns) {
      result.states[i] = InputState::kStale;
      continue;
    }
    fresh.push_back(i);
  }
  if (fresh.empty()) {
    return result;
  }

  // the first fresh input defines frame and geometry
  const GridSnapshot & ref = inputs[fresh.front()];
  result.reference = static_cast<int>(fresh.front());

  std::vector<size_t> used;
  for (const size_t i : fresh) {
    const GridSnapshot & in = inputs[i];
    if (in.frame_id == ref.frame_id && sameGeometry(in.geometry, ref.geometry)) {
      result.states[i] = InputState::kUsed;
      used.push_back(i);
    } else {
      result.states[i] = InputState::kIncompatible;
    }
  }
  result.used = used.size();
  if (used.size() < std::max<size_t>(min_inputs, 1)) {
    return result;
  }

  // oldest first, so "latest" lets the newest grid win; ties keep the configured order
  std::stable_sort(
    used.begin(), used.end(), [&inputs](size_t a, size_t b) {
      return inputs[a].received_ns < inputs[b].received_ns;
    });
  std::vector<const std::vector<signed char> *> layers;
  for (const size_t i : used) {
    layers.push_back(&inputs[i].cells);
  }
  result.cells = fuseLayers(rule, layers);
  return result;
}

}  // namespace grid_fusion
