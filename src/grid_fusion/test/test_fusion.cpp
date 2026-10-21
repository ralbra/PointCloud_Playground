#include <gtest/gtest.h>

#include <cstdint>
#include <limits>
#include <memory>
#include <string>
#include <vector>

#include "builtin_interfaces/msg/time.hpp"
#include "grid_map_msgs/msg/grid_map.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "grid_fusion/fusion.hpp"

using namespace grid_fusion;

namespace
{
using Cells = std::vector<signed char>;
constexpr signed char U = kUnknownCell;
constexpr int64_t kSec = 1000000000LL;

Cells fuse(FusionRule rule, const std::vector<Cells> & layers)
{
  std::vector<const Cells *> ptrs;
  for (const auto & l : layers) {
    ptrs.push_back(&l);
  }
  return fuseLayers(rule, ptrs);
}

// A one-row grid; enough for fuseSnapshots, which never touches the message pointers.
GridSnapshot makeSnapshot(
  const Cells & cells, int64_t received_ns,
  const std::string & frame = "map", double resolution = 1.0)
{
  GridSnapshot s;
  s.received_ns = received_ns;
  s.frame_id = frame;
  s.cells = cells;
  s.geometry.resolution = resolution;
  s.geometry.length_x = static_cast<double>(cells.size()) * resolution;
  s.geometry.length_y = resolution;
  s.geometry.cell_count = cells.size();
  return s;
}

grid_map_msgs::msg::GridMap makeGridMapMsg(const std::vector<float> & values)
{
  grid_map_msgs::msg::GridMap msg;
  msg.header.frame_id = "map";
  msg.info.resolution = 1.0;
  msg.info.length_x = static_cast<double>(values.size());
  msg.info.length_y = 1.0;
  msg.info.pose.orientation.w = 1.0;
  msg.layers.push_back("intensity");
  msg.data.resize(1);
  msg.data[0].data = values;
  return msg;
}
}  // namespace

// ------------------------------------------------------------- topics

TEST(JoinTopic, JoinsPrefixAndName)
{
  EXPECT_EQ(joinTopic("front", "intensity_grid"), "front/intensity_grid");
  EXPECT_EQ(joinTopic("/front/", "intensity_grid"), "/front/intensity_grid");
  EXPECT_EQ(joinTopic("a/b", "x"), "a/b/x");
  EXPECT_EQ(joinTopic("/", "x"), "/x");
  EXPECT_EQ(joinTopic("", "x"), "x");
}

// -------------------------------------------------------------- rules

TEST(FusionRuleParsing, AcceptsAllNamesAndRejectsOthers)
{
  FusionRule rule = FusionRule::Max;
  EXPECT_TRUE(parseFusionRule("min", rule));
  EXPECT_EQ(rule, FusionRule::Min);
  EXPECT_TRUE(parseFusionRule("sum", rule));
  EXPECT_EQ(rule, FusionRule::Sum);
  EXPECT_TRUE(parseFusionRule("mean", rule));
  EXPECT_EQ(rule, FusionRule::Mean);
  EXPECT_TRUE(parseFusionRule("latest", rule));
  EXPECT_EQ(rule, FusionRule::Latest);
  EXPECT_TRUE(parseFusionRule("max", rule));
  EXPECT_EQ(rule, FusionRule::Max);

  EXPECT_FALSE(parseFusionRule("Max", rule));
  EXPECT_FALSE(parseFusionRule("average", rule));
  EXPECT_FALSE(parseFusionRule("", rule));
}

TEST(FusionRuleParsing, NamesRoundTrip)
{
  const FusionRule all[] = {FusionRule::Max, FusionRule::Min, FusionRule::Sum, FusionRule::Mean,
    FusionRule::Latest};
  for (const FusionRule r : all) {
    FusionRule parsed = FusionRule::Max;
    ASSERT_TRUE(parseFusionRule(fusionRuleName(r), parsed));
    EXPECT_EQ(parsed, r);
  }
}

// ---------------------------------------------------------- fuseLayers

TEST(FuseLayers, EachRuleCombinesKnownCellsOnly)
{
  const Cells a = {10, U, 50, U};
  const Cells b = {20, 30, U, U};

  EXPECT_EQ(fuse(FusionRule::Max, {a, b}), (Cells{20, 30, 50, U}));
  EXPECT_EQ(fuse(FusionRule::Min, {a, b}), (Cells{10, 30, 50, U}));
  EXPECT_EQ(fuse(FusionRule::Sum, {a, b}), (Cells{30, 30, 50, U}));
  EXPECT_EQ(fuse(FusionRule::Mean, {a, b}), (Cells{15, 30, 50, U}));
}

TEST(FuseLayers, LatestTakesTheNewestKnownValuePerCell)
{
  const Cells a = {10, U, 50, U};
  const Cells b = {20, 30, U, U};

  EXPECT_EQ(fuse(FusionRule::Latest, {a, b}), (Cells{20, 30, 50, U}));  // b is newest
  EXPECT_EQ(fuse(FusionRule::Latest, {b, a}), (Cells{10, 30, 50, U}));  // a is newest
}

TEST(FuseLayers, SingleLayerPassesThroughForEveryRule)
{
  const Cells layer = {5, U, -7};
  const FusionRule all[] = {FusionRule::Max, FusionRule::Min, FusionRule::Sum, FusionRule::Mean,
    FusionRule::Latest};
  for (const FusionRule r : all) {
    EXPECT_EQ(fuse(r, {layer}), layer) << fusionRuleName(r);
  }
}

TEST(FuseLayers, SumSaturatesInsteadOfWrapping)
{
  EXPECT_EQ(fuse(FusionRule::Sum, {Cells{100}, Cells{100}}), (Cells{127}));
  EXPECT_EQ(fuse(FusionRule::Sum, {Cells{-100}, Cells{-100}}), (Cells{-127}));
}

TEST(FuseLayers, MeanRoundsToNearestAwayFromZero)
{
  EXPECT_EQ(fuse(FusionRule::Mean, {Cells{1}, Cells{2}}), (Cells{2}));
  EXPECT_EQ(fuse(FusionRule::Mean, {Cells{-1}, Cells{-2}}), (Cells{-2}));
  EXPECT_EQ(fuse(FusionRule::Mean, {Cells{1}, Cells{1}, Cells{2}}), (Cells{1}));
}

TEST(FuseLayers, EmptyAndMismatchedInput)
{
  EXPECT_TRUE(fuseLayers(FusionRule::Max, {}).empty());

  const Cells a = {1, 2, 3};
  const Cells b = {9, 9};  // shorter: its missing cells are skipped
  EXPECT_EQ(fuse(FusionRule::Max, {a, b}), (Cells{9, 9, 3}));
}

// ------------------------------------------------------------ geometry

TEST(Geometry, SameGeometryComparesEveryField)
{
  GridGeometry a;
  a.resolution = 0.5;
  a.length_x = 20.0;
  a.length_y = 30.0;
  a.pos_x = 10.0;
  a.pos_y = 15.0;
  a.ori_z = 1.0;
  a.ori_w = 0.0;
  a.cell_count = 2400;

  GridGeometry b = a;
  EXPECT_TRUE(sameGeometry(a, b));
  b.pos_x += 1e-9;
  EXPECT_TRUE(sameGeometry(a, b));  // within tolerance

  b = a; b.resolution = 0.25;   EXPECT_FALSE(sameGeometry(a, b));
  b = a; b.length_x = 21.0;     EXPECT_FALSE(sameGeometry(a, b));
  b = a; b.length_y = 31.0;     EXPECT_FALSE(sameGeometry(a, b));
  b = a; b.pos_y = 16.0;        EXPECT_FALSE(sameGeometry(a, b));
  b = a; b.ori_z = 0.0;         EXPECT_FALSE(sameGeometry(a, b));
  b = a; b.cell_count = 2399;   EXPECT_FALSE(sameGeometry(a, b));
}

TEST(Geometry, TransposedGridsAreNotTheSame)
{
  nav_msgs::msg::OccupancyGrid a;
  a.info.resolution = 1.0f;
  a.info.width = 4;
  a.info.height = 3;
  a.data.assign(12, 0);
  nav_msgs::msg::OccupancyGrid b = a;
  b.info.width = 3;
  b.info.height = 4;
  EXPECT_FALSE(sameGeometry(geometryOf(a), geometryOf(b)));
}

// ----------------------------------------------------- message conversion

TEST(Conversion, GridMapValueToCell)
{
  EXPECT_EQ(gridMapValueToCell(1.0f), 127);
  EXPECT_EQ(gridMapValueToCell(0.0f), 0);
  EXPECT_EQ(gridMapValueToCell(-128.0f / 127.0f), U);
  EXPECT_EQ(gridMapValueToCell(64.0f / 127.0f), 64);
  EXPECT_EQ(gridMapValueToCell(std::numeric_limits<float>::quiet_NaN()), U);
  EXPECT_EQ(gridMapValueToCell(std::numeric_limits<float>::infinity()), U);
  EXPECT_EQ(gridMapValueToCell(5.0f), 127);    // clamped
  EXPECT_EQ(gridMapValueToCell(-5.0f), -128);  // clamped
}

TEST(Conversion, GridMapWithoutLayersHasNoCells)
{
  grid_map_msgs::msg::GridMap msg;
  EXPECT_TRUE(cellsOf(msg).empty());
}

TEST(Conversion, FillThenReadBackGivesTheSameCells)
{
  const Cells cells = {127, 0, U, 64, -50};
  auto msg = makeGridMapMsg(std::vector<float>(cells.size(), 0.0f));
  ASSERT_TRUE(fillGridMap(msg, cells, "map", builtin_interfaces::msg::Time()));
  EXPECT_EQ(cellsOf(msg), cells);
}

TEST(Conversion, FillOccupancyGridCopiesCellsFrameAndStamp)
{
  nav_msgs::msg::OccupancyGrid grid;
  builtin_interfaces::msg::Time stamp;
  stamp.sec = 5;
  stamp.nanosec = 7u;

  fillOccupancyGrid(grid, {1, 2, 3}, "map", stamp);

  EXPECT_EQ(grid.header.frame_id, "map");
  EXPECT_EQ(grid.header.stamp.sec, 5);
  EXPECT_EQ(grid.header.stamp.nanosec, 7u);
  EXPECT_EQ(grid.info.map_load_time.sec, 5);
  EXPECT_EQ(grid.data, (Cells{1, 2, 3}));
}

TEST(Conversion, FillGridMapRefusesWrongSizes)
{
  auto msg = makeGridMapMsg({42.0f, 42.0f, 42.0f, 42.0f});
  EXPECT_FALSE(fillGridMap(msg, {1, 2, 3}, "map", builtin_interfaces::msg::Time()));
  for (const float v : msg.data[0].data) {
    EXPECT_FLOAT_EQ(v, 42.0f);
  }

  grid_map_msgs::msg::GridMap no_layer;
  EXPECT_FALSE(fillGridMap(no_layer, {1}, "map", builtin_interfaces::msg::Time()));
}

// ----------------------------------------------------------- snapshots

TEST(Snapshot, OccupancyGridKeepsGeometryFrameAndCells)
{
  auto grid = std::make_shared<nav_msgs::msg::OccupancyGrid>();
  grid->header.frame_id = "map";
  grid->info.resolution = 0.5f;
  grid->info.width = 3;
  grid->info.height = 2;
  grid->info.origin.position.x = 1.0;
  grid->info.origin.orientation.z = 1.0;
  grid->data = {1, 2, 3, 4, 5, 6};

  const GridSnapshot s = snapshotOf(grid, 99);

  EXPECT_EQ(s.received_ns, 99);
  EXPECT_EQ(s.frame_id, "map");
  EXPECT_EQ(s.cells, (Cells{1, 2, 3, 4, 5, 6}));
  EXPECT_DOUBLE_EQ(s.geometry.length_x, 1.5);
  EXPECT_DOUBLE_EQ(s.geometry.length_y, 1.0);
  EXPECT_DOUBLE_EQ(s.geometry.pos_x, 1.0);
  EXPECT_DOUBLE_EQ(s.geometry.ori_z, 1.0);
  EXPECT_EQ(s.geometry.cell_count, 6u);
  EXPECT_NE(s.occupancy, nullptr);
}

TEST(Snapshot, OccupancyGridWithInconsistentSizeIsUnusable)
{
  auto grid = std::make_shared<nav_msgs::msg::OccupancyGrid>();
  grid->info.width = 3;
  grid->info.height = 2;
  grid->data = {1, 2, 3, 4, 5};  // one cell short
  EXPECT_TRUE(snapshotOf(grid, 1).cells.empty());
}

TEST(Snapshot, GridMapIsConvertedToCells)
{
  auto msg = std::make_shared<grid_map_msgs::msg::GridMap>(
    makeGridMapMsg({1.0f, 0.0f, -128.0f / 127.0f}));
  const GridSnapshot s = snapshotOf(msg, 7);
  EXPECT_EQ(s.cells, (Cells{127, 0, U}));
  EXPECT_EQ(s.geometry.cell_count, 3u);
  EXPECT_NE(s.grid_map, nullptr);
}

// ------------------------------------------------------ fuseSnapshots

TEST(FuseSnapshots, CombinesAllFreshInputs)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({10, 20}, 9 * kSec),
    makeSnapshot({30, U}, 10 * kSec)};
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 1);

  EXPECT_EQ(r.cells, (Cells{30, 20}));
  EXPECT_EQ(r.used, 2u);
  EXPECT_EQ(r.reference, 0);
  EXPECT_EQ(r.states[0], InputState::kUsed);
  EXPECT_EQ(r.states[1], InputState::kUsed);
}

TEST(FuseSnapshots, StalledInputIsExcluded)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({10, 20}, 9 * kSec),
    makeSnapshot({99, 99}, 5 * kSec)};
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 1);

  EXPECT_EQ(r.cells, (Cells{10, 20}));
  EXPECT_EQ(r.used, 1u);
  EXPECT_EQ(r.states[1], InputState::kStale);
}

TEST(FuseSnapshots, TimeoutBoundaryIsInclusive)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({1}, 8 * kSec)};

  auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 1);
  EXPECT_EQ(r.states[0], InputState::kUsed);  // age == timeout

  r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec + 1, 2 * kSec, 1);
  EXPECT_EQ(r.states[0], InputState::kStale);  // one nanosecond older
}

TEST(FuseSnapshots, InputsFromTheFutureCountAsStale)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({1}, 10 * kSec)};
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 5 * kSec, 2 * kSec, 1);  // clock jumped back
  EXPECT_EQ(r.states[0], InputState::kStale);
  EXPECT_TRUE(r.cells.empty());
}

TEST(FuseSnapshots, InputWithoutDataIsReportedAsSuch)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({1, 2}, 10 * kSec), GridSnapshot()};
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 1);
  EXPECT_EQ(r.cells, (Cells{1, 2}));
  EXPECT_EQ(r.states[1], InputState::kNoData);
}

TEST(FuseSnapshots, MinInputsBlocksOutputButStillReportsStates)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({1, 2}, 10 * kSec),
    makeSnapshot({3, 4}, 1 * kSec)};
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 2);

  EXPECT_TRUE(r.cells.empty());
  EXPECT_EQ(r.used, 1u);
  EXPECT_EQ(r.states[0], InputState::kUsed);
  EXPECT_EQ(r.states[1], InputState::kStale);
}

TEST(FuseSnapshots, AllStalledGivesNoOutputAndNoReference)
{
  const std::vector<GridSnapshot> inputs =
  {makeSnapshot({1}, 1 * kSec), makeSnapshot({2}, 2 * kSec)};
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 1);
  EXPECT_TRUE(r.cells.empty());
  EXPECT_EQ(r.reference, -1);
  EXPECT_EQ(r.used, 0u);
}

TEST(FuseSnapshots, DifferentFrameIsIncompatible)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({1, 2}, 10 * kSec, "map"),
    makeSnapshot({3, 4}, 10 * kSec, "odom")};
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 1);
  EXPECT_EQ(r.cells, (Cells{1, 2}));
  EXPECT_EQ(r.states[1], InputState::kIncompatible);
}

TEST(FuseSnapshots, DifferentGeometryIsIncompatible)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({1, 2}, 10 * kSec, "map", 1.0),
    makeSnapshot({3, 4}, 10 * kSec, "map", 0.5)};
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 1);
  EXPECT_EQ(r.states[1], InputState::kIncompatible);
  EXPECT_EQ(r.used, 1u);
}

TEST(FuseSnapshots, ReferenceIsTheFirstFreshInputNotTheFirstConfigured)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({9, 9}, 1 * kSec, "map"),    // stale
    makeSnapshot({1, 2}, 10 * kSec, "map"),                                           // reference
    makeSnapshot({3, 4}, 10 * kSec, "odom")};                                          // mismatch
  const auto r = fuseSnapshots(inputs, FusionRule::Max, 10 * kSec, 2 * kSec, 1);

  EXPECT_EQ(r.reference, 1);
  EXPECT_EQ(r.states[0], InputState::kStale);
  EXPECT_EQ(r.states[1], InputState::kUsed);
  EXPECT_EQ(r.states[2], InputState::kIncompatible);
  EXPECT_EQ(r.cells, (Cells{1, 2}));
}

TEST(FuseSnapshots, LatestFollowsReceiveTimeNotConfiguredOrder)
{
  const std::vector<GridSnapshot> inputs = {makeSnapshot({10}, 9 * kSec),   // newer
    makeSnapshot({20}, 8 * kSec)};                                          // older
  const auto r = fuseSnapshots(inputs, FusionRule::Latest, 10 * kSec, 5 * kSec, 1);
  EXPECT_EQ(r.cells, (Cells{10}));
}
