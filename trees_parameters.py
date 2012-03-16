# -----------------------------------------------------------------------------------------------------------------
# Terasology Trees: A proof-of-concept dynamic object oriented tree generator for the Terasology project.

# Copyright 2012 Cynthia Kurtz <cfkurtz@kurtz-fernhout.com>.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------------------------------------------

import sys

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# BIOMASS

# Biomass is undifferentiated plant material, which includes living tissues and plant
# sugars used to store energy. All tree parst contain, require and use biomass. It serves
# as the "currency" into which all new growth is converted as it is passed around the tree.

# Each tree part has a starting biomass, which it had when it was created by a meristem
# or internode, and an optimal biomass, which it seeks to obtain (by making photosynthate
# in the case of leaves, by pleading in the case of everything else). Each tree part
# uses up some small amount of biomass each day through maintenance respiration, 
# and if the "stock" of living biomass in any part goes below its (parameterized) minimum,
# it dies. Death does not make a tree part disappear, just change color/block ID into a
# dead form. This is to prevent things from blipping out of existence and also to
# create harvestable "dry wood" or "dry leaves" blocks that might be uniquely useful.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

START_MERISTEM_BIOMASS = [1.0, 1.0]
# The amount of biomass deposited in a meristem when it is first created.
# Note: for all parameters that impact both stems and roots, the first in the list is stems, the second is roots.
# Note: The "unit" for biomass is ... meaningless, magical, made up.
# (In real crop simulation models it is usually tons per hectare or some other
# measure of mass per area of soil surface. Alternatively it could be simply mass.)
# min: above the death level by a few days' worth; should always be lower than the optimum
# max: can make this number large if you want the tree to grow very fast (it is like having a very nutrient-rich seed)

BIOMASS_TO_MAKE_ONE_PHYTOMER = [10.0, 8.0]
# The amount of biomass the meristem needs to accumulate before it can produce one phytomer.
# A phytomer is a modular plant growth unit made up of one internode (stem section) and some number
# of leaves and buds stuck to it.
# For the root, a phytomer is the same except with no leaves, so the requirement is usually somewhat lower.
# min: better not make it zero: the thing will ballooon too fast. make it at least a few more than the start biomass
# max: the higher the number the slower the growth, so very large numbers may produce very small trees

BIOMASS_TO_MAKE_ONE_FLOWER_CLUSTER = 10.0
# The amount of biomass the meristem needs to accumulate before it can produce one cluster of flowers,
# when the tree is in reproductive mode and the meristem has "gone reproductive".
# min: 1 or 2 more than what the meristem has at the start
# max: for a tree with only one flower cluster, you could make this huge, but then you might never get any

BIOMASS_USED_BY_MERISTEM_PER_DAY = [0.1, 0.1]
# The amount of biomass the meristem uses up in maintenance respiration per day.
# min: if you want the tree to survive anything, you can set this to zero
# max: a very sensitive  or hard to grow tree would have high maintenance levels, maybe even up to 1 or 2

MERISTEM_DIES_IF_BIOMASS_GOES_BELOW = [0.01, 0.01]
# How little biomass a meristem can have before it kicks the bucket.
# min: a tree that can never die could have this set at zero
# max: a hard-to-please tree could have this set higher, say 1.0

START_INTERNODE_BIOMASS = [1.0, 1.0]
OPTIMAL_INTERNODE_BIOMASS = [13.0, 13.0]
BIOMASS_USED_BY_INTERNODE_PER_DAY = [0.1, 0.1]
INTERNODE_DIES_IF_BIOMASS_GOES_BELOW = [0.01, 0.01]

START_LEAF_CLUSTER_BIOMASS = 1
OPTIMAL_LEAF_CLUSTER_BIOMASS = 8
BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY = 0.5
LEAF_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01

START_FLOWER_CLUSTER_BIOMASS = 1.0
OPTIMAL_FLOWER_CLUSTER_BIOMASS = 4.0
BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY = 0.1
FLOWER_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01

START_FRUIT_CLUSTER_BIOMASS = 1.0
OPTIMAL_FRUIT_CLUSTER_BIOMASS = 12.0
BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY = 0.1
FRUIT_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# PHOTOSYNTHESIS

# Leaf clusters produce photosynthate (from photosynthesis). This drives all growth in the tree,
# because all new biomass comes from it.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

OPTIMAL_DAILY_PHOTOSYNTHATE = 30.0
# How much biomass (plant materials plus energy stored as sugars) is produced by one
# leaf cluster in one day in perfectly optimal conditions. Biomass is dimensionless,
# or more like it uses some fictional metric like "biomass units" which are internally
# consistent but externally meaningless ("magic numbers"). This parameter needs to
# synch up with all the other biomass parameters (optimal, used, dies) to produce
# trees that don't all die at birth. If one of these goes up or down the others 
# will need to keep pace, unless you want to change how hardy or large the tree grows.
# min and max depend on the other biomass parameters; use trial and error to find out
# what works.

WATER_FOR_OPTIMAL_PHOTOSYNTHESIS = 2.0
# The amount of water at which photosynthesis is optimal. As with biomass this
# has no metric, BUT it has to synch up with how the water is allocated in the soil,
# or trees will not grow.
# min and max depend on the water distribution system in the soil.

MINERALS_FOR_OPTIMAL_PHOTOSYNTHESIS = 2.0
# Same as for water.

NUM_BLOCKS_ABOVE_FOR_MAX_SHADE_STRESS = 5
# The number of blocks above a leaf cluster considered maximally obstructing of sunlight.
# Could vary based on the size of individual leaves.
# min: if zero, no shade stress can take place (any number of leaves will not shade the plant)
# max: as many blocks as you like; the more blocks the less shade stress

LOW_SUN_AND_SHADE_TOLERANCE = 0.5
WATER_STRESS_TOLERANCE = 1.0
MINERAL_STRESS_TOLERANCE = 1.0
# These three factors determine how tolerant the tree species is to conditions that
# hamper growth. A tolerance of zero for any factor will make that species maximally
# sensitive; a tolerance of one will make it indifferent to that factor.
# So for example a species with tolerances of 0, 1 and 0 for sun, water and minerals
# respectively would be drought-resistant, requiring no water, but would be intolerant
# of shade or poor soils. A species with all ones would grow optimally anywhere,
# even in darkness. 
# min: 0.0 for no tolerance and maximum sensitivity
# max: 1.0 for full tolerance and no sensitivity

LEAF_SENESCENCE_BEGINS_AT_AGE = 30
# Leaves eventually lose their photosynthetic efficiency through simple age.
# This will eventually limit the growth of the tree, since it will also exhaust
# the available supplies of water and minerals (if they don't resupply themselves).
# So senescence acts as a brake on the eventual size of trees.
# min: if this was set to zero the tree could not grow at all, so it has to allow some time
# max: set this very high to make the tree grow (theoretically) forever 

LEAF_SENESCENCE_LASTS = 30
# How long it takes a leaf, after it has started its senescence phase, to stop
# photosynthesizing entirely. This doesn't meant the leaf will die, just that it will
# produce less and less photosynthate. 
# min: set to zero to produce instant senescence (which is not realistic)
# max: set to a huge number to prevent loss of efficiency

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# UPTAKE

# Root internodes take up water and minerals from the soil.
# In this simulation water and mineral deposits in the soil are randomly generated in patches,
# but in a blocky world these would be found in the ground by block type.
# Another set of parameters not necessary here but critical there would be
# what block IDs the tree species considers to hold water and minerals, and how much.
# For example, a "gold tree" might only grow where it can find gold blocks.
# Or a tree species might consider there to be available water in water blocks,
# but also in dirt, clay, stone, and even sand, to diminishing degrees.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

ROOT_WATER_EXTRACTION_EFFICIENCY = 0.25
# How much of the water it finds in any particular block of ground the root meristem can take up.
# min: if you set this to zero the tree will never grow, so it should be at least something like 0.2
# max: if you set this to 1.0 the tree will suck all water it finds up immediately and grow as fast as possible,
# which could be a good thing if water is ephemeral or competition is strong.

ROOT_MINERAL_EXTRACTION_EFFICIENCY = 0.25
# The same thing as for water, but for minerals.

ROOT_WATER_EXTRACTION_RADIUS = 3
# How far in the block space the root meristem can reach (from its tip, or endLocation) to extract
# water from the soil. Basically the root tip draws all the water in the cube so specified
# (multiplied by its efficiency) and reduces the amount in that cube by the same amount.
# You could have water extraction take effect by changing block IDs, 
# say from water to dirt to clay to stone to sand.
# min: if the radius is zero the tree will be less "hardy", having to have been placed in exactly 
# the right spot to find water; but you could do it.
# max: if this is too high it is not really realistic, but you could set this as high 
# (say for a "super sucker" tree) to 10 or even 100 
# must be an integer

ROOT_MINERAL_EXTRACTION_RADIUS = 3
# The same thing as for water, but for minerals.
# must be an integer

NON_WOODY_INTERNODES_SEEK_RESOURCES_IN_RADIUS = [2, 2]
# This simulates the seeking behavior of stem and root tips as they "feel around" the environment
# looking for sun (stem tips) or water and minerals (root tips). This does cause the stems
# to "jump around" as they grow, but to keep it from making the whole tree contort wildly,
# the behavior is confined to non-woody internodes, which have the flexibility to explore.
# min: set to zero this will turn off seeking behavior
# max: very large numbers are not realistic, because they could cause internodes to expand
# ridiculous distances in search of resources; probably this should not be set higher than about four
# must be an integer

INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS = [8, 8]
# When internodes turn woody they "harden" and stop seeking resources by moving around the space.
# min: to keep the entire tree flexible forever, set this number very high
# max: to turn off seeking entirely set this number to zero 
# must be an integer

ROOTS_CAN_GROW_THIS_MANY_BLOCKS_ABOVE_GROUND = 0
# Allows aerial roots if set above zero. This means nothing but that they can grow
# above the level set as ground level. Any root internodes above the ground cannot
# draw on water or minerals, because they have ventured outside the deposits;
# so if they seek water and minerals they may not stay above ground.
# min: if zero, no roots go above ground (this is the normal case); if above zero,
# produces aerial roots; if below zero, keeps all root branches below that level
# max: probably would look strange if this was very high!
# must be an integer

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# DISTRIBUTION

# These parameters determine how the tree responds to stress conditions by remobilizing
# photosynthate to parts of the tree that can help remedy the situation.

# The parameters in this section are more advanced, in that changing them might 
# break plant growth entirely. Still, they can be changed to create species that respond
# differently to the conditions they find.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

MIN_STRESS_TO_TRIGGER_BIOMASS_REDISTRIBUTION = 0.5
# Each day the tree calculates its most pressing need: for sun, water or minerals.
# If that maximum stress factor exceeds this amount, the tree will remobilize its
# biomass (not water or minerals) to respond to the crisis. Thus the parameter 
# defines to what extent the tree responds to prevailing conditions by varying
# its growth pattern.
# min: 0.0 means the tree will ALWAYS choose one of the stress-induced mobilization patterns
# min: 1.0 means the tree will NEVER choose a stress-induced pattern (will be inflexible)

BIOMASS_DISTRIBUTION_SPREAD = {}
# Spread is how much of the available biomass goes to each possible recipient
# waiting in line to get it. Thus if this is set at 0.5, for example, half the
# available biomass goes to the first in line, 0.25 to the next, 0.125 to the next, etc.
# This does mean that, given the limited pool of applicants (generally not more than or 10)
# there may be some biomass left over undistributed at the end of the day.
# But usually that will be not much, and it can be given out the next day.

BIOMASS_DISTRIBUTION_ORDER = {}
# This determines (for a particular stress condition) in what order the applicants
# for available biomass line up to receive it. Note the two arrays, the first for stems
# and the second for roots.

# Normal growth favors leaves and growing stems and a wide spread of biomass.
BIOMASS_DISTRIBUTION_SPREAD["no stress"] = [0.4, 0.4]
BIOMASS_DISTRIBUTION_ORDER["no stress"] = [
	["leaves", "child", "branches", "root", "axillary meristems", "apical meristems", "flowers", "fruits", ],
	["axillary meristems", "apical meristems", "branches", "child", "above-ground tree",],
	]

# In low light or shade conditions, the above-ground tree shunts biomass to developing meristems 
# so new stems can develop and reach for the light. Root biomass distribution is unaffected.
BIOMASS_DISTRIBUTION_SPREAD["low sun and shade"] = [0.7, 0.4]
BIOMASS_DISTRIBUTION_ORDER["low sun and shade"] = [
	["child", "apical meristems", "axillary meristems", "leaves", "branches", "root", "flowers", "fruits", ],
	["axillary meristems", "apical meristems", "branches", "child", "above-ground tree",],
	]

# In conditions of water or mineral stress, biomass is shunted down to the roots so they can grow
# to find more water and/or minerals.
BIOMASS_DISTRIBUTION_SPREAD["water or mineral stress"] = [0.7, 0.7]
BIOMASS_DISTRIBUTION_ORDER["water or mineral stress"] = [
	["root", "parent", "child", "branches", "axillary meristems", "apical meristems", "leaves", "fruits", "flowers", ],
	["child", "apical meristems", "axillary meristems", "branches",  "above-ground tree",],
	]

# When the tree enters reproductive mode, everything moves to the flowers, then fruits
# even extra biomass in the roots is pulled up to be used for reproduction.
# Stress factors are put aside as all means are sent to reproduction (for good or ill).
BIOMASS_DISTRIBUTION_SPREAD["reproduction"] = [0.7, 0.7]
BIOMASS_DISTRIBUTION_ORDER["reproduction"] = [
	["flowers", "fruits", "child", "branches", "leaves", "axillary meristems", "apical meristems", "root", ],
	["above-ground tree", "parent", "child", "apical meristems", "axillary meristems", "branches", ],
	]

# The distribution of water and minerals is the same in all conditions, because it is dependent on the
# workings of the xylem and phloem. (At least, I can find a lot of information on the remobilization 
# of plant MATTER in response to stress conditions, but nothing on the remobilization of actual
# water or minerals. Methinks plants are limited in how much they can pump water by the laws
# of physics and gravity and so on. It would also complicate the model a lot more and add several
# more complex parameters.
WATER_DISTRIBUTION_SPREAD_PERCENT = [0.4, 0.4]
WATER_DISTRIBUTION_ORDER = [["leaves", "child", 'branches'], ["above-ground tree", 'parent'],]

MINERALS_DISTRIBUTION_SPREAD_PERCENT = [0.4, 0.4]
MINERALS_DISTRIBUTION_ORDER = [["leaves", "child", 'branches'],["above-ground tree", 'parent'],]

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# BRANCHING

# These parameters determine how the tree will form a shape, mainly by changing how meristems are placed
# and how they become active.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


AXILLARY_MERISTEMS_PER_INTERNODE = [2, 2]
# How many leaves and buds come off the stem at each internode. 
# One is an "opposite" leaf arrangement, two is "alternate", three or more is "whorled". 
# min: 1
# max: any number, but above six or so you will not see much difference, and simulation will
# slow down a lot.

BRANCHING_PROBABILITY_OFF_TRUNK = [0.5, 0.5]
# How likely it is that any particular axillary meristem on the trunk will create a new branch.
# The higher these numbers, the branchier the above-ground tree and root. 
# For example, for a tap root set the root branching probability to zero.
# min: 0.0
# max: 1.0 but watch out that might be a huge tree...

BRANCHING_PROBABILITY_NOT_OFF_TRUNK = [0.5, 0.5]
# The same, but for meristems not found on the main trunk (stem or root) of the tree.

APICAL_DOMINANCE_OFF_TRUNK = [6, 6]
# Apical dominance is a phenomonenon in plants where the apical meristem sends a hormone down the stem
# that inhibits the development of axillary meristems on it.
# This parameter determines how far the "hormone" goes before it peters out.
# Note that if the branching probability is very low, this parameter will have no effect.
# The two parameters work together to produce the overall "growth habit" of the tree.
# Note that if the apical bud gets snipped off and is absent, the apical dominance will disappear for that branch.
# This parameter applies only to buds on the main trunk of the tree.
# min: 0 would be no apical dominance whatsoever, as though there were no apical bud.

APICAL_DOMINANCE_NOT_OFF_TRUNK = [6, 6]
# The same, but for meristems not found on the main trunk (stem or root) of the tree.

MAX_NUM_INTERNODES_ON_TREE_EVER = [100, 100] 
# This is not really a parameter, but more like a check on all the other parameters, 
# to prevent a badly chosen set from creating a tree so giant it puts too much stress on the system.
# min: if you wanted a type of tree that only produced very small things, you could set this as low as 10 or so
# max: probably best to keep this lower than 100 or so, though a "giant tree" type could go higher

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# REPRODUCTION

# The reproductive model here is very simple: on a particular day, the tree sends a signal
# around that tells all or some meristems to stop working on vegetative growth and start
# working on building flowers.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

REPRODUCTIVE_MODE_STARTS_ON_DAY = 20
# When the tree starts producing flowers. On this day any meristems that exist will consult
# the parameters below to decide if they should switch their growth mode/intent over to
# reproduction, after which all biomass they accumulate will go toward producing a flower cluster.
# Note that I have this set very low for testing, but it would normally be much higher.
# min: set at zero to start the plant flowering right away (but that is unrealistic)
# max: set at a very high number to prevent reproduction entirely

PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.25
PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.25
# Determinate growth in plants means that once a plant has switched over to reproduction
# it produces no more vegetative growth. Indeterminate growth means the plant keeps producing
# new shoots as well as flowers and fruits. So, to create determinate growth, set this
# probability (for apical and/or axillary meristems) to 1.0. To allow the tree to keep
# growing after it starts flowering, set the probability to less than 1.0.
# To prevent flowering entirely you can set both of these to zero.
# min: 1.0, max: 1.0

MINIMUM_DAYS_FLOWER_APPEARS_EVEN_WITH_OPTIMAL_BIOMASS = 6
# Flower clusters are not meristems, but they keep track of biomass accumulated 
# toward the creation of fruits, which can only be created once the flower cluster
# has reached its full biomass (ignoring inconvenient things like fertilization...).
# However, sometimes if a tree is growing very well there might be so much extra biomass
# floating around that the flowers don't have time to appear before they "fill up"
# and create fruits. This parameter just makes sure flowers appear.
# For an interesting challenge, setting this parameter low, even to zero, would mean
# that flowers (which might have desirable properties) would be hard to obtain.
# min: 0 
# max: as many as you like. set to a huge number to make no fruits at all.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# DRAWING: LENGTHS, WIDTHS, ANGLES

# The drawing parameters produce the look of the tree: how tall and thick it is, what angles it places.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK = [9.0, 4.0]
# How long a fully-formed internode is, in block-space distance (not necessarily in blocks,
# since the distance may be diagonally placed). 
# min: for stems, best to keep this to at least 3, to have room for the leaves and buds on the side(s)
# max: no particular limit, except that if the tree hits up against the bounds of the vertical space
# it could look strange or be cut off (but that might be acceptable in some cases)
# all lengths/widths/distances can be real numbers, though rounding takes place as blocks are occupied

INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH = [9.0, 4.0]
# The same, but for internodes not on the main trunk

INTERNODE_LENGTH_AT_CREATION = [3.0, 2.0] 
# How long an internode is when it first appears on the tree.
# min: for stems, best to keep this to at least 3, to have room for the leaf clusters and buds on the side(s);
# for roots it should be at least two to have room for the buds
# max: no particular limit

FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE = [10.0, 8.0]
# The very first internode on the plant (stem or root) may be longer or shorter than the others
# to achieve a particular shape.
# min and max: same as for the other internodes

FIRST_INTERNODE_LENGTH_AT_CREATION = [5.0, 5.0]
# Same as for the full size parameter.
# min and max: same as for the other internodes

INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE = [0.0, 0.0]
# How wide each internode is in diameter when it has reached its full biomass.
# min: one block
# max: if setting this very wide (>10 or so) best to keep the stems hollow, otherwise
# the processing of so many blocks may bog things down considerably

INTERNODE_WIDTH_AT_CREATION = [1.0, 1.0]
# How wide each internode is when it is created (or has no biomass).
# min: one block. minimum should always be smaller than maximum (for all such parameters).
# max: no limit except on processing

INTERNODES_ARE_HOLLOW = [True, True]
# Whether internodes occupy all of the space they map out or whether they only occupy the outside.
# Has no effect when internode width is set low (1 or 2). 
# When solid internodes are not required, this speeds up growth.

INTERNODE_LINE_DRAWING_METHOD = "solid"
# By what algorithm internode lines are interpolated through voxel space.
# Choose from "solid" (inclusive of both sides of floating-point positions, thicker when the line is diagonal),
# "sparse" (a thin line, possibly missing some corner turnings where the floating-point position is close to an edge),
# "spiral" (a sort of spiraling line that meanders as it goes, making the stem easier to climb)

INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER = 1.5
# With what fineness of detail to draw internode lines. The higher the multiplier the more perfect the 
# internode shape, but the slower the simulation will run. At low numbers (<1.0) there may be gaps and "floating" blocks,
# especially on thin diagonal internodes; at higher numbers (>2.0) internodes will appear more solid,
# but the speed of block calculation will slow considerably.
# min: at zero the internode will draw nothing at all! at 0.25 there will be many gaps
# max: above something like 3 the slow speed will become unbearable if there are a lot of internodes;
# generally a reasonable range is between 0.5 and 2.0

ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [45, 45]
# The angle at which branches develop off the main trunk of the tree (top-side or root), in degrees.
# min: you would probably want this to be at least ten degrees
# max: to get drooping-down branches, set this above 90 degrees; above 180 it would start to wrap around again

ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [30, 30]
# The angle at which branches that are NOT off the main trunk develop.
# If you look at real trees, they usually have a larger angle coming off the trunk, 
# and the angle gets smaller as the branches get smaller. Having two parameters makes that look better.
# min: even just a few degrees is all right
# max: same as above. Note that this is the angle coming off the parent branch, so the 
# resulting branch could end up going in strange directions. 

RANDOM_INTERNODE_SWAY = [10.0, 10.0]
# Adds a random angle of sway to each internode when created, to simulate variation in growth.
# min: for a completely ordered tree set these to zero
# max: no maximum really, but you will get very strange trees if this is set very high
# all angles can be real numbers

LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
LEAF_CLUSTER_LENGTH_AT_CREATION = 1.0
LEAF_CLUSTER_ANGLE_WITH_STEM = 40.0
RANDOM_LEAF_CLUSTER_SWAY = 20.0

FLOWER_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
FLOWER_CLUSTER_LENGTH_AT_CREATION = 1.0
FLOWER_CLUSTER_ANGLE_WITH_STEM = 20.0
RANDOM_FLOWER_CLUSTER_SWAY = 10.0

FRUIT_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 2.0
FRUIT_CLUSTER_LENGTH_AT_CREATION = 1.0
FRUIT_CLUSTER_ANGLE_WITH_STEM = 80.0
RANDOM_FRUIT_CLUSTER_SWAY = 20.0


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# DRAWING: SHAPES

# All of the three clusters (leaf, flower, fruit) are made up of a "spine" which extends
# in one direction, plus any number of "wings" that rotate around to form a sort of 3D
# grouping of blocks that represents a shape. Note that when the length of any of these
# parameters is exactly one (at creation and optimally), no shape is calculated, but a single block is placed.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

LEAF_CLUSTER_SHAPE_PATTERN = "12321"
# Specifies cluster shape by marking a number of blocks out to the side (from the spine) 
# to place blocks, symmetrically. Things that grow on plants/trees
# are usually either bilaterally or radially symmetrical, so this creates those patterns
# using a system that should be easy to use. For example, a leaf with serrated edges might have a
# pattern like "121212", or a leaf that starts large and gets small at the tip 
# might have a pattern like "4321". 
# Since the pattern will repeat to match the spine length,
# you don't need to specify the whole length: "12" will work as well as "121212". 
# Note, however, that if you want a pattern that covers the whole spine, you should
# specify at least one longer than your "leaf cluster length" because the line may be
# longer in blocks than it is in length. So if you want 4-long leaf clusters
# with the pattern 4321, specify a parameter of "43211" or even "432111" to prevent
# the 4 from coming back around again on diagonal lines.
# no min and max: must be a string sequence of numbers.
# Note that the length of the "wings" off the "spine" as specified here
# is affected by leaf-cluster biomass, so leaves on a small or poorly growing tree
# will not be as wide as you specify.
# This may not be the most elegant shape-forming system ever created ...

LEAF_CLUSTER_SIDES = 1
# This, along with the shape pattern, determines what each cluster looks like.
# For a leaf cluster the usual practice will be to place two bilaterally symmetrical wings 
# to create a plane (which represents not a leaf but all the twigs and leaves at the end of a branch),
# but you could have stranger leaf clusters if you wanted to.
# must be an integer
# min: 1 
# max: probably above 8 or so repetitions the results will be indistinguishable

LEAF_CLUSTERS_ARE_HOLLOW = False
# All the tree parts that CAN be drawn as a 3D "blob" can be solid or hollow.
# Hollow parts could be used as houses or could hold water (if a parameter was set).

FLOWER_CLUSTER_SHAPE_PATTERN = "12344"
FLOWER_CLUSTER_SIDES = 5
FLOWER_CLUSTERS_ARE_HOLLOW = True

FRUIT_CLUSTER_SHAPE_PATTERN = "1232"
FRUIT_CLUSTER_SIDES = 6
FRUIT_CLUSTERS_ARE_HOLLOW = True

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# DRAWING - COLORS

# All of the colors specified here are stand-ins for block identities, which define
# what you see when you look at a tree, and what you get when you harvest parts of it. 
# Some IDs might be unique, such as dead root apical meristem of a particular tree species
# (and maybe that would be a block that has some unique properties).
# Some might be of a common class, such as any dead tree material of an unspecified nature.
# Some might be other blocks, like the fruits of the gold tree being gold blocks.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

COLOR_MERISTEM = ["#00FF00", "#CC7F32"]
COLOR_MERISTEM_DEAD = ["#8B8B83", "#000000"]

COLOR_INTERNODE_WOODY = ["#CC7F32", "#CC7F32"]
COLOR_INTERNODE_NONWOODY = ["#8B7500", "#CC7F32"]
COLOR_INTERNODE_DEAD = ["#292421", "#CC7F32"]

COLOR_LEAF_CLUSTER = "#488214"
COLOR_LEAF_CLUSTER_DEAD = "#5E2605"

COLOR_FLOWER_CLUSTER = "#FFE303"
COLOR_FLOWER_CLUSTER_DEAD = "#5E2605"

COLOR_FRUIT_CLUSTER = "#CD0000"
COLOR_FRUIT_CLUSTER_DEAD = "#5E2605"

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# TEST "SPECIES" PARAMETER SETS

# Of course you would not really read in parameters this way; you would read them 
# from data files, bound each value with a reasonable min and max (so it would be hard to break
# the model), and give any non-specified parameters a default value.
# I just did it this way because I ran out of time to do it right.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Here I have chosen a few of our "amazing trees" from the "terasology_tree_notes.rtf" file
# and tried to partially implement them. All of these could be improved given more time
# and most imply some additional links between the tree growth model and the rest of the game.

# Note: All these tree species have parameters that make them grow far too fast for the game.
# This is just because I couldn't stand to wait long enough for any plant to grow to 1000 days old.
# But in the real game a plant that takes 1000 days to grow to its full size would be fine.
# So in integration these parameters would have to be shifted down, particularly those
# that generate massive amounts of photosynthate for new growth.

#SPECIES = "Lift tree"
#SPECIES = "Spiral tree"
#SPECIES = "Bulb tree"
#SPECIES = "Hobble tree"
#SPECIES = "Taproot tree"
#SPECIES = "Christmas tree"

if len(sys.argv) > 1: 
	SPECIES = sys.argv[1]
else:
	SPECIES = "default"

ALL_SPECIES = ["Lift tree", "Spiral tree", "Bulb tree", 'Hobble tree', "Taproot tree", "Christmas tree"]
	
if SPECIES == "Lift tree":
	# Notes from  "terasology tree notes" file
	# Name: Lift tree
	# Like: sequoia	
	# Exaggerations: Not only is it super tall, but sometimes there is a ladder inside you can climb up. 
	# Also, real sequoias have whole ecologies growing in their branches. This could happen in the lift tree. 
	# Special animals, special foods ... There might even be pre-built houses in them, high up.	
	# Useful for: Quick safety when traveling. Instant houses. Just really interesting places to discover.	
	# Could burrow through (to some extent) without killing it. (Like sequoias with car tunnels in them.) 
	# Could live in them.	
	# Dangers: Could fall from high up.
	# Left to do to make this work: Make it have a ladder inside. Make leaf/flower/fruit parts include
	# dirt/grass blocks (that things can grow on). Make it grow slowly.
	# BRANCHING
	AXILLARY_MERISTEMS_PER_INTERNODE = [1, 1]
	BRANCHING_PROBABILITY_OFF_TRUNK = [0.0, 0.5]
	BRANCHING_PROBABILITY_NOT_OFF_TRUNK = [0.0, 0.5]
	APICAL_DOMINANCE_OFF_TRUNK = [0, 6]
	APICAL_DOMINANCE_NOT_OFF_TRUNK = [0, 6]
	# REPRODUCTION
	REPRODUCTIVE_MODE_STARTS_ON_DAY = 20
	PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 1.0
	PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.0
	MINIMUM_DAYS_FLOWER_APPEARS_EVEN_WITH_OPTIMAL_BIOMASS = 6
	# DRAWING: LENGTHS, WIDTHS, ANGLES
	# internodes
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK = [30.0, 6.0]
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH = [3.0, 6.0]
	INTERNODE_LENGTH_AT_CREATION = [6.0, 2.0] 
	FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE = [45.0, 13.0]
	FIRST_INTERNODE_LENGTH_AT_CREATION = [20.0, 5.0]
	INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE = [3.0, 3.0]
	INTERNODES_ARE_HOLLOW = [True, True]
	ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [45, 45]
	ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [30, 30]
	RANDOM_INTERNODE_SWAY = [5.0, 10.0]
	INTERNODE_LINE_DRAWING_METHOD = "solid"
	INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER = 0.5
	# leaf clusters
	LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 12.0
	LEAF_CLUSTER_ANGLE_WITH_STEM = 120.0
	RANDOM_LEAF_CLUSTER_SWAY = 40.0
	
elif SPECIES == "Spiral tree":
	# Name: Spiral tree
	# Like: various trees that grow in spiral patterns	
	# Uses: You can walk up the staircase. Quick look around.
	# Maybe you could encourage them to grow in particular directions, then graft different 
	# spiral trees together to create an above-ground transportation network, on which rail cars could move.	
	# Dangers: Could fall but not likely; leaves would protect you
	# BRANCHING
	AXILLARY_MERISTEMS_PER_INTERNODE = [1, 1]
	BRANCHING_PROBABILITY_OFF_TRUNK = [0.5, 0.25]
	BRANCHING_PROBABILITY_NOT_OFF_TRUNK = [0.3, 0.25]
	APICAL_DOMINANCE_OFF_TRUNK = [3, 6]
	APICAL_DOMINANCE_NOT_OFF_TRUNK = [3, 6]
	# REPRODUCTION
	REPRODUCTIVE_MODE_STARTS_ON_DAY = 20
	PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.0
	PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.8
	MINIMUM_DAYS_FLOWER_APPEARS_EVEN_WITH_OPTIMAL_BIOMASS = 3
	# UPTAKE
	NON_WOODY_INTERNODES_SEEK_RESOURCES_IN_RADIUS = [10, 2] # extremely bendy
	INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS = [100, 8] # and they stay bendy
	# DRAWING: LENGTHS, WIDTHS, ANGLES
	# internodes
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK = [5.0, 6.0]
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH = [15.0, 6.0]
	INTERNODE_LENGTH_AT_CREATION = [1.0, 1.0] 
	FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE = [10.0, 13.0]
	FIRST_INTERNODE_LENGTH_AT_CREATION = [1.0, 5.0]
	INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE = [1.0, 1.0]
	INTERNODE_WIDTH_AT_CREATION = [1.0, 1.0]
	ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [90, 45]
	ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [90, 30]
	RANDOM_INTERNODE_SWAY = [40.0, 10.0]
	INTERNODE_LINE_DRAWING_METHOD = "spiral"
	INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER = 2.5
	# leaf clusters
	LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 3.0
	LEAF_CLUSTER_ANGLE_WITH_STEM = 80.0
	RANDOM_LEAF_CLUSTER_SWAY = 40.0
	# flower clusters
	FLOWER_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
	FLOWER_CLUSTER_ANGLE_WITH_STEM = 20.0
	RANDOM_FLOWER_CLUSTER_SWAY = 10.0
	# fruit clusters
	FRUIT_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
	FRUIT_CLUSTER_ANGLE_WITH_STEM = 80.0
	RANDOM_FRUIT_CLUSTER_SWAY = 20.0
	
elif SPECIES == "Bulb tree":
	# Name: Bulb tree
	# Like: baobab	
	# Exaggeration: Has spherical bulb in center, but it's really really big. 
	# Uses: Can be a house (or prison). Sometimes contains water (useful in desert).	
	# If you hollow out the center carefully, it will grow larger. 	
	# Rare and only found in deserts; very slow growth.
	# Dangers: Could get trapped inside somehow, could drown inside.
	# BRANCHING
	AXILLARY_MERISTEMS_PER_INTERNODE = [1, 1]
	BRANCHING_PROBABILITY_OFF_TRUNK = [0.2, 0.25]
	BRANCHING_PROBABILITY_NOT_OFF_TRUNK = [0.0, 0.25]
	APICAL_DOMINANCE_OFF_TRUNK = [8, 4]
	APICAL_DOMINANCE_NOT_OFF_TRUNK = [8, 4]
	# REPRODUCTION
	REPRODUCTIVE_MODE_STARTS_ON_DAY = 20
	PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.6
	PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.0
	MINIMUM_DAYS_FLOWER_APPEARS_EVEN_WITH_OPTIMAL_BIOMASS = 10
	# DRAWING: LENGTHS, WIDTHS, ANGLES
	# internodes
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK = [8.0, 6.0]
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH = [5.0, 6.0]
	INTERNODE_LENGTH_AT_CREATION = [1.0, 2.0] 
	FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE = [50.0, 13.0]
	FIRST_INTERNODE_LENGTH_AT_CREATION = [1.0, 5.0]
	INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE = [6.0, 6.0]
	INTERNODE_WIDTH_AT_CREATION = [1.0, 1.0]
	ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [90, 45]
	ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [90, 30]
	RANDOM_INTERNODE_SWAY = [10.0, 10.0]
	INTERNODE_LINE_DRAWING_METHOD = "solid"
	INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER = 0.5
	# leaf clusters
	LEAF_CLUSTER_SHAPE_PATTERN = "465"
	LEAF_CLUSTER_SIDES = 5
	LEAF_CLUSTERS_ARE_HOLLOW = False
	LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 10.0
	LEAF_CLUSTER_LENGTH_AT_CREATION = 1.0
	LEAF_CLUSTER_ANGLE_WITH_STEM = 30.0
	RANDOM_LEAF_CLUSTER_SWAY = 20.0
	# flower clusters
	FLOWER_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
	FLOWER_CLUSTER_LENGTH_AT_CREATION = 1.0
	FLOWER_CLUSTER_ANGLE_WITH_STEM = 20.0
	RANDOM_FLOWER_CLUSTER_SWAY = 10.0
	# fruit clusters
	FRUIT_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
	FRUIT_CLUSTER_LENGTH_AT_CREATION = 1.0
	FRUIT_CLUSTER_ANGLE_WITH_STEM = 80.0
	RANDOM_FRUIT_CLUSTER_SWAY = 20.0
	
elif SPECIES == "Hobble tree":
	# Name: Hobble tree
	# Like: Pirangi cashew tree, hobblebush
	# Exaggeration: Tree branches come back down to the ground and re-root, 
	# making a sort of "basket" shape surrounding an area
	# Uses: Can be a frame for a house. Can trap monsters. 
	# Could encourage them to grow in a regular pattern to make a better trap?	
	# Found near streams; fast growth.
	# Dangers: Could get stuck inside? When running fast could get lost in maze of branches touching ground.
	# BRANCHING
	AXILLARY_MERISTEMS_PER_INTERNODE = [8, 1]
	BRANCHING_PROBABILITY_OFF_TRUNK = [0.2, 0.25]
	BRANCHING_PROBABILITY_NOT_OFF_TRUNK = [0.0, 0.25]
	APICAL_DOMINANCE_OFF_TRUNK = [1, 4]
	APICAL_DOMINANCE_NOT_OFF_TRUNK = [0, 4]
	# DRAWING: LENGTHS, WIDTHS, ANGLES
	# internodes
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK = [2.0, 6.0]
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH = [12.0, 6.0]
	INTERNODE_LENGTH_AT_CREATION = [3.0, 2.0] 
	FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE = [10.0, 13.0]
	FIRST_INTERNODE_LENGTH_AT_CREATION = [5.0, 5.0]
	ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [150, 45]
	ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [10, 30]
	RANDOM_INTERNODE_SWAY = [50.0, 10.0]
	INTERNODE_LINE_DRAWING_METHOD = "sparse"
	INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER = 1.0
	# leaf clusters
	LEAF_CLUSTER_SHAPE_PATTERN = "1232"
	LEAF_CLUSTER_SIDES = 2
	LEAF_CLUSTERS_ARE_HOLLOW = False
	LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 3.0
	LEAF_CLUSTER_LENGTH_AT_CREATION = 1.0
	LEAF_CLUSTER_ANGLE_WITH_STEM = 90.0
	RANDOM_LEAF_CLUSTER_SWAY = 10.0
	# flower clusters
	FLOWER_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
	FLOWER_CLUSTER_LENGTH_AT_CREATION = 1.0
	FLOWER_CLUSTER_ANGLE_WITH_STEM = 20.0
	RANDOM_FLOWER_CLUSTER_SWAY = 10.0
	# fruit clusters
	FRUIT_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
	FRUIT_CLUSTER_LENGTH_AT_CREATION = 1.0
	FRUIT_CLUSTER_ANGLE_WITH_STEM = 80.0
	RANDOM_FRUIT_CLUSTER_SWAY = 20.0
	
elif SPECIES == "Taproot tree":
	# Name: Tap tree
	# Like: desert trees with very long tap roots	
	# Exaggeration: Tree has huge root that goes down far into the earth.	
	# Uses: Could burrow down in tree to mine. Wood is easier to break/cut than stone, hence mining is easier. 
	# Also a safe base away from monsters.	Can hollow out base if you are careful. Can get water there also. 
	# Can encourage tree to grow tap root deeper by reducing nearby water supplies or manipulating underground water supplies.
	# .Could drown; could fall down into bottom of root. 
	# Rarely one of them will grow right out the bottom of the world. Could die if too much water is removed nearby.
	# Name: Hobble tree
	# Like: Pirangi cashew tree, hobblebush
	# Exaggeration: Tree branches come back down to the ground and re-root, 
	# making a sort of "basket" shape surrounding an area
	# Uses: Can be a frame for a house. Can trap monsters. 
	# Could encourage them to grow in a regular pattern to make a better trap?	
	# Found near streams; fast growth.
	# Dangers: Could get stuck inside? When running fast could get lost in maze of branches touching ground.
	# BRANCHING
	AXILLARY_MERISTEMS_PER_INTERNODE = [2, 2]
	BRANCHING_PROBABILITY_OFF_TRUNK = [0.25, 0.0]
	BRANCHING_PROBABILITY_NOT_OFF_TRUNK = [0.25, 0.0]
	APICAL_DOMINANCE_OFF_TRUNK = [4, 40]
	APICAL_DOMINANCE_NOT_OFF_TRUNK = [4, 40]
	# DRAWING: LENGTHS, WIDTHS, ANGLES
	# internodes
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK = [6.0, 6.0]
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH = [4.0, 0.0]
	INTERNODE_LENGTH_AT_CREATION = [1.0, 1.0] 
	FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE = [4.0, 13.0]
	FIRST_INTERNODE_LENGTH_AT_CREATION = [1.0, 1.0]
	INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE = [1.0, 2.0]
	INTERNODE_WIDTH_AT_CREATION = [1.0, 1.0]
	ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [45, 45]
	ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [30, 30]
	RANDOM_INTERNODE_SWAY = [20.0, 0.0]
	INTERNODE_LINE_DRAWING_METHOD = "solid"
	INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER = 0.5
	INTERNODES_ARE_HOLLOW = [True, False]
	# leaf clusters
	LEAF_CLUSTER_SHAPE_PATTERN = "12"
	LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 3.0
	LEAF_CLUSTER_ANGLE_WITH_STEM = 30.0
	RANDOM_LEAF_CLUSTER_SWAY = 10.0
	
elif SPECIES == "Christmas tree":
	# xxx
	# BRANCHING
	AXILLARY_MERISTEMS_PER_INTERNODE = [4, 4]
	BRANCHING_PROBABILITY_OFF_TRUNK = [0.7, 0.2]
	BRANCHING_PROBABILITY_NOT_OFF_TRUNK = [0.25, 0.2]
	APICAL_DOMINANCE_OFF_TRUNK = [8, 4]
	APICAL_DOMINANCE_NOT_OFF_TRUNK = [1, 4]
	# DRAWING: LENGTHS, WIDTHS, ANGLES
	# internodes
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK = [12.0, 6.0]
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH = [4.0, 4.0]
	INTERNODE_LENGTH_AT_CREATION = [1.0, 1.0] 
	FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE = [4.0, 4.0]
	FIRST_INTERNODE_LENGTH_AT_CREATION = [1.0, 1.0]
	INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE = [1.0, 1.0]
	INTERNODE_WIDTH_AT_CREATION = [1.0, 1.0]
	ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [100, 45]
	ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [10, 30]
	RANDOM_INTERNODE_SWAY = [10.0, 10.0]
	INTERNODE_LINE_DRAWING_METHOD = "solid"
	INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER = 1.0
	# leaf clusters
	LEAF_CLUSTER_SHAPE_PATTERN = "2"
	LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 3.0
	LEAF_CLUSTER_ANGLE_WITH_STEM = 30.0
	RANDOM_LEAF_CLUSTER_SWAY = 10.0
	
# this one is just to draw parameters from
elif SPECIES == "default":
	# BIOMASS
	# meristem
	START_MERISTEM_BIOMASS = [1.0, 1.0]
	BIOMASS_TO_MAKE_ONE_PHYTOMER = [10.0, 8.0]
	BIOMASS_TO_MAKE_ONE_FLOWER_CLUSTER = 10.0
	BIOMASS_USED_BY_MERISTEM_PER_DAY = [0.1, 0.1]
	MERISTEM_DIES_IF_BIOMASS_GOES_BELOW = [0.01, 0.01]
	# internode
	START_INTERNODE_BIOMASS = [1.0, 1.0]
	OPTIMAL_INTERNODE_BIOMASS = [13.0, 13.0]
	BIOMASS_USED_BY_INTERNODE_PER_DAY = [0.1, 0.1]
	INTERNODE_DIES_IF_BIOMASS_GOES_BELOW = [0.01, 0.01]
	# leaf cluster
	START_LEAF_CLUSTER_BIOMASS = 1
	OPTIMAL_LEAF_CLUSTER_BIOMASS = 8
	BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY = 0.5
	LEAF_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01
	# flower cluster
	START_FLOWER_CLUSTER_BIOMASS = 1.0
	OPTIMAL_FLOWER_CLUSTER_BIOMASS = 4.0
	BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY = 0.1
	FLOWER_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01
	# fruit cluster
	START_FRUIT_CLUSTER_BIOMASS = 1.0
	OPTIMAL_FRUIT_CLUSTER_BIOMASS = 12.0
	BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY = 0.1
	FRUIT_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01
	# PHOTOSYNTHESIS
	OPTIMAL_DAILY_PHOTOSYNTHATE = 30.0
	WATER_FOR_OPTIMAL_PHOTOSYNTHESIS = 2.0
	MINERALS_FOR_OPTIMAL_PHOTOSYNTHESIS = 2.0
	NUM_BLOCKS_ABOVE_FOR_MAX_SHADE_STRESS = 5
	LOW_SUN_AND_SHADE_TOLERANCE = 0.5
	WATER_STRESS_TOLERANCE = 1.0
	MINERAL_STRESS_TOLERANCE = 1.0
	LEAF_SENESCENCE_BEGINS_AT_AGE = 30
	LEAF_SENESCENCE_LASTS = 30
	# UPTAKE
	ROOT_WATER_EXTRACTION_EFFICIENCY = 0.25
	ROOT_MINERAL_EXTRACTION_EFFICIENCY = 0.25
	ROOT_WATER_EXTRACTION_RADIUS = 3
	ROOT_MINERAL_EXTRACTION_RADIUS = 3
	NON_WOODY_INTERNODES_SEEK_RESOURCES_IN_RADIUS = [2, 2]
	INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS = [8, 8]
	ROOTS_CAN_GROW_THIS_MANY_BLOCKS_ABOVE_GROUND = 0
	# BRANCHING
	AXILLARY_MERISTEMS_PER_INTERNODE = [2, 2]
	BRANCHING_PROBABILITY_OFF_TRUNK = [0.5, 0.5]
	BRANCHING_PROBABILITY_NOT_OFF_TRUNK = [0.5, 0.5]
	APICAL_DOMINANCE_OFF_TRUNK = [6, 6]
	APICAL_DOMINANCE_NOT_OFF_TRUNK  = [6, 6]
	MAX_NUM_INTERNODES_ON_TREE_EVER = [100, 100] 
	# REPRODUCTION
	REPRODUCTIVE_MODE_STARTS_ON_DAY = 20
	PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.25
	PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.25
	MINIMUM_DAYS_FLOWER_APPEARS_EVEN_WITH_OPTIMAL_BIOMASS = 6
	# DRAWING: LENGTHS, WIDTHS, ANGLES
	# internodes
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK = [12.0, 6.0]
	INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH = [12.0, 6.0]
	INTERNODE_LENGTH_AT_CREATION = [3.0, 2.0] 
	FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE = [15.0, 13.0]
	FIRST_INTERNODE_LENGTH_AT_CREATION = [5.0, 5.0]
	INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE = [1.0, 1.0]
	INTERNODE_WIDTH_AT_CREATION = [1.0, 1.0]
	INTERNODES_ARE_HOLLOW = [True, True]
	ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [45, 45]
	ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [30, 30]
	RANDOM_INTERNODE_SWAY = [10.0, 10.0]
	INTERNODE_LINE_DRAWING_METHOD = "solid"
	INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER = 1.5
	# leaf clusters
	LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
	LEAF_CLUSTER_LENGTH_AT_CREATION = 1.0
	LEAF_CLUSTER_ANGLE_WITH_STEM = 40.0
	RANDOM_LEAF_CLUSTER_SWAY = 20.0
	# flower clusters
	FLOWER_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 4.0
	FLOWER_CLUSTER_LENGTH_AT_CREATION = 1.0
	FLOWER_CLUSTER_ANGLE_WITH_STEM = 20.0
	RANDOM_FLOWER_CLUSTER_SWAY = 10.0
	# fruit clusters
	FRUIT_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE = 2.0
	FRUIT_CLUSTER_LENGTH_AT_CREATION = 1.0
	FRUIT_CLUSTER_ANGLE_WITH_STEM = 80.0
	RANDOM_FRUIT_CLUSTER_SWAY = 20.0
	# DRAWING: SHAPES
	LEAF_CLUSTER_SHAPE_PATTERN = "12321"
	LEAF_CLUSTER_SIDES = 2
	LEAF_CLUSTERS_ARE_HOLLOW = False
	FLOWER_CLUSTER_SHAPE_PATTERN = "12344"
	FLOWER_CLUSTER_SIDES = 5
	FLOWER_CLUSTERS_ARE_HOLLOW = True
	FRUIT_CLUSTER_SHAPE_PATTERN = "1232"
	FRUIT_CLUSTER_SIDES = 6
	FRUIT_CLUSTERS_ARE_HOLLOW = True
	# DRAWING - COLORS
	COLOR_MERISTEM = ["#00FF00", "#CC7F32"]
	COLOR_MERISTEM_DEAD = ["#8B8B83", "#000000"]
	COLOR_INTERNODE_WOODY = ["#CC7F32", "#CC7F32"]
	COLOR_INTERNODE_NONWOODY = ["#8B7500", "#CC7F32"]
	COLOR_INTERNODE_DEAD = ["#292421", "#CC7F32"]
	COLOR_LEAF_CLUSTER = "#488214"
	COLOR_LEAF_CLUSTER_DEAD = "#5E2605"
	COLOR_FLOWER_CLUSTER = "#FFE303"
	COLOR_FLOWER_CLUSTER_DEAD = "#5E2605"
	COLOR_FRUIT_CLUSTER = "#CD0000"
	COLOR_FRUIT_CLUSTER_DEAD = "#5E2605"

	
