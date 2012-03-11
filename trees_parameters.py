# -----------------------------------------------------------------------------------------------------------------
# proof-of-concept dynamic object oriented tree generator 
# for terasology project
# written by cynthia kurtz
# -----------------------------------------------------------------------------------------------------------------

from trees_constants import *

# Note: If you read the comments in this file from top to bottom you will understand it better.
# The lower comments assume understandings from above so as to avoid massive repetition.

# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# MERISTEMS
# Meristems are buds. They are the part-making factories of the tree.
# They shoud be visible and take up a whole block, because trimming (snipping) meristems
# would be a way to manipulate the growth of the tree.
# An important distinction in meristems is whether they are apical, or at the apex (end
# of the stem), or axillary, or in the angle between leaf and stem (the axil). 
# When apical meristems develop they produce a longer stem.
# When axillary meristems develop they produce branches.
# -------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------
# MERISTEMS - BIOMASS
# -------------------------------------------------------------------------------------------

START_MERISTEM_BIOMASS = [1, 1]
# The amount of biomass deposited in a meristem when it is first created.
# Note: for all parameters that impact both stems and roots, the first in the list is stems, the second is roots.
# Note: The "unit" for biomass is ... meaningless, so nothing.
# min: above the death level by a few days' worth
# max: can make this number large if you want the plant to grow very fast (it is like having a very nutrient-rich seed)

BIOMASS_TO_MAKE_ONE_PHYTOMER = [10, 8]
# The amount of biomass the meristem needs to accumulate before it can produce one phytomer.
# A phytomer is a modular plant growth unit made up of one internode (stem section) and some number
# of leaves and buds stuck to it.
# For the root, a phytomer is the same except with no leaves, so the requirement is usually somewhat lower.
# min: better not make it zero: the thing will ballooon too fast. make it at least a few more than the start biomass
# max: if too high, nothing will grow

BIOMASS_TO_MAKE_ONE_FLOWER_CLUSTER = 10
# The amount of biomass the meristem needs to accumulate before it can produce one cluster of flowers,
# when the plant is in reproductive mode and the meristem has "gone reproductive".
# min: 1 or 2 more than what the meristem has at the start
# max: for a tree with only one flower cluster, you could make this huge, but then you might never get any

BIOMASS_USED_BY_MERISTEM_PER_DAY = [0.1, 0.1]
# The amount of biomass the meristem uses up in maintenance respiration per day.
# min: if you want the tree to survive anything, you can set this to zero
# max: a very sensitive  or hard to grow tree would have high maintenance levels, maybe even up to 1 or 2

MERISTEM_DIES_IF_BIOMASS_GOES_BELOW = [0.01, 0.01]
# How little biomass a meristem can have before it kicks the bucket.
# min: a plant that can never die could have this set at zero
# max: a hard-to-please plant could have this set higher, say 1.0

# -------------------------------------------------------------------------------------------
# MERISTEMS - BRANCHING
# -------------------------------------------------------------------------------------------

AXILLARY_MERISTEMS_PER_INTERNODE = [2, 2]
# How many leaves and buds come off the stem at each internode. 
# One is an "opposite" leaf arrangement, two is "alternate", three or four is "whorled". 
# min: 1
# max: 4

BRANCHING_PROBABILITY = [0.5, 0.5]
# How likely it is that any particular axillary meristem will create a new branch.
# The higher these numbers, the branchier the above-ground tree and root. 
# For example, for a tap root set the root branching probability to zero.
# min: 0.0
# max: 1.0 but watch out that might be a huge tree... 

APICAL_DOMINANCE_EXTENDS_FOR = [3, 2]
# Apical dominance is a phenomonenon in plants where the apical meristem sends a hormone down the stem
# that inhibits the development of axillary meristems on it.
# This parameter determines how far the "hormone" goes before it peters out.
# Note that if the branching probability is very low, this parameter will have no effect.
# The two parameters work together to produce the overall "growth habit" of the tree.
# Note that if the apical bud gets snipped off and is absent, the apical dominance will disappear for that branch.
# min: 0 would be no apical dominance whatsoever, as though there were no apical bud.

ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = [45, 40]
# The angle at which branches develop off the main trunk of the tree (top-side or root), in degrees.
# min: you would probably want this to be at least ten degrees
# max: to get drooping-down branches, set this above 90 degrees; above 180 it would start to wrap around again

ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = [45, 20]
# The angle at which branches that are NOT off the main trunk develop.
# If you look at real trees, they usually have a larger angle coming off the trunk, 
# and the angle gets smaller as the branches get smaller. Having two parameters makes that look better.
# min: even just a few degrees is all right
# max: same as above. Note that this is the angle coming off the parent branch, so the 
# resulting branch could end up going in strange directions. 

MAX_NUM_INTERNODES_ON_TREE_EVER = [100, 100] 
# This is not really a parameter, but more like a check on all the other parameters, 
# to prevent a badly chosen set from creating a tree so giant it puts too much stress on the system.
# min: if you wanted a type of tree that only produced very small things, you could set this as low as 10 or so
# max: probably best to keep this lower than 100 or so, though a "giant tree" type could go higher

# -------------------------------------------------------------------------------------------
# MERISTEMS - DRAWING
# -------------------------------------------------------------------------------------------

COLOR_MERISTEM = ["#7CFC00", "#000000"]
# Here the color of each type of tree part stands in for a block type in a blocky world.

COLOR_MERISTEM_DEAD = ['b', 'b']# ["#8B8B83", "#000000"]
# Note that you might want to have separate (perhaps especially desirable) block types 
# for dead tree parts. 

# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# INTERNODES
# An internode is a section of stem between "nodes" where leaves and axillary meristems
# come off the stem. Together these make a phytomer or modular plant unit.
# Internodes are the plant's piping system: they transport water, minerals and plant sugars
# (here lumped in with plant tissues as "biomass") throughout the plant.
# -------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------
# INTERNODES - BIOMASS
# -------------------------------------------------------------------------------------------

START_INTERNODE_BIOMASS = [1, 1]
# How much biomass an internode has when it is created. 
# min: usually 1, but to give a "boost" to the plant set it higher
# max: at a high number (say greater than 5 or so) this will produce a much too large tree

OPTIMAL_INTERNODE_BIOMASS = [16, 13]
# How much biomass it takes for an internode to grow to its full size (length and width).
# min: should be no smaller than what the internode has when it is created
# max: the higher the number the slower the growth, so a very large number (say >100) may produce too-small trees

BIOMASS_USED_BY_INTERNODE_PER_DAY = [0.1, 0.1]
# How much biomass the internode "burns through" in a day.
# min: could be set to zero, for a tree that cannot die
# max: set high for a hard-to-grow tree

INTERNODE_DIES_IF_BIOMASS_GOES_BELOW = [0.01, 0.01]
# Same as with the meristem.

# -------------------------------------------------------------------------------------------
# INTERNODES - ROOT UPTAKE
# Root internodes take up water and minerals from the soil.
# In this simulation water and mineral deposits in the soil are randomly generated in patches,
# but in Terasology these would be found in the ground by block type.
# Another set of parameters not necessary here but critical there would be
# what block IDs the tree species considers to hold water and minerals, and how much.
# For example, a "gold tree" might only grow where it can find gold blocks.
# Or a tree species might consider there to be available water in water blocks,
# but also in dirt, clay, stone, and even sand, to diminishing degrees.
# -------------------------------------------------------------------------------------------

ROOT_WATER_EXTRACTION_EFFICIENCY = 0.25
# How much of the water it finds in any particular block of ground the root meristem can take up.
# min: if you set this to zero the tree will never grow, so it should be at least something like 0.2
# max: if you set this to 1.0 the tree will suck all water it finds up immediately and grow as fast as possible,
# which could be a good thing if water is ephemeral or competition is strong.

ROOT_MINERAL_EXTRACTION_EFFICIENCY = 0.25
# The same thing as for water, but for minerals.

ROOT_WATER_EXTRACTION_RADIUS = 2
# How far in the block space the root meristem can reach (from its tip, or endLocation) to extract
# water from the soil. Basically the root tip draws all the water in the cube so specified
# (multiplied by its efficiency) and reduces the amount in that cube by the same amount.
# In Terasology you could have water extraction take effect by changing block IDs, 
# say from water to dirt to clay to stone to sand.
# min: if the radius is zero the tree will be less "hardy", having to have been placed in exactly 
# the right spot to find water; but you could do it
# max: if this is too high it is not really realistic, but you could set this as high 
# (say for a "super sucker" tree) to 10 or even 100 

ROOT_MINERAL_EXTRACTION_RADIUS = 2
# The same thing as for water, but for minerals.

# -------------------------------------------------------------------------------------------
# INTERNODES - GROWTH
# These parameters determine how the internodes take up space.
# -------------------------------------------------------------------------------------------

INTERNODES_SEEK_SUN_OR_WATER_AND_MINERALS_IN_RADIUS = [0,0]
INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS = [8,8]
ROOTS_CAN_GROW_THIS_MANY_BLOCKS_ABOVE_GROUND = 0

# -------------------------------------------------------------------------------------------
# INTERNODES - DRAWING
# -------------------------------------------------------------------------------------------

INTERNODE_LENGTH_AT_CREATION = [3, 3] # no less than 3, to have room for buds and leafClusters
INTERNODE_LENGTH_AT_FULL_SIZE = [20, 6]
INTERNODE_WIDTH_AT_CREATION = [1, 1]
INTERNODE_WIDTH_AT_FULL_SIZE = [1, 1]
FIRST_INTERNODE_LENGTH_AT_CREATION = [5, 5]
FIRST_INTERNODE_LENGTH_AT_FULL_SIZE = [15, 13]
RANDOM_INTERNODE_SWAY = [20, 20]
COLOR_INTERNODE_WOODY = "#CC7F32" # root not needed
COLOR_INTERNODE_NONWOODY = ["#8B7500", "#CC7F32"]
COLOR_INTERNODE_DEAD = ['b', 'b']# ["#292421", "#CC7F32"]

# -------------------------------------------------------------------------------------------
# LEAF CLUSTERS
# -------------------------------------------------------------------------------------------

# LEAF CLUSTERS - BIOMASS
START_LEAF_CLUSTER_BIOMASS = 1
OPTIMAL_LEAF_CLUSTER_BIOMASS = 8
BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY = 0.5
LEAF_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01

# LEAF CLUSTERS - PHOTOSYNTHESIS
OPTIMAL_LEAF_PHOTOSYNTHATE = 40
WATER_FOR_OPTIMAL_PHOTOSYNTHESIS = 5
MINERALS_FOR_OPTIMAL_PHOTOSYNTHESIS = 5
LOW_SUN_TOLERANCE = 0.5
SHADE_TOLERANCE = 0.5
WATER_STRESS_TOLERANCE = 0.5
MINERAL_STRESS_TOLERANCE = 0.5

# LEAF CLUSTERS - DRAWING
LEAF_CLUSTER_LENGTH_AT_FULL_SIZE = 4
LEAF_CLUSTER_LENGTH_AT_CREATION = 1
LEAF_CLUSTER_ANGLE_WITH_STEM = 40
LEAF_CLUSTER_SHAPE_ANGLE = 30
RANDOM_LEAF_CLUSTER_SWAY = 20
LEAF_CLUSTER_SHAPE_PATTERN = "12"
LEAF_CLUSTER_SIDES = 4
COLOR_LEAF_CLUSTER = "#488214"
COLOR_LEAF_CLUSTER_DEAD = 'b' #"#5E2605"

# -------------------------------------------------------------------------------------------
# FLOWER CLUSTERS
# -------------------------------------------------------------------------------------------

# FLOWER CLUSTERS - BIOMASS
START_FLOWER_CLUSTER_BIOMASS = 1
OPTIMAL_FLOWER_CLUSTER_BIOMASS = 8
BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY = 0.1
FLOWER_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01

# FLOWER CLUSTERS - TIMING
REPRODUCTIVE_MODE_STARTS_ON_DAY = 20
# cfk mention determinate vs indeterminate
PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.5
PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE = 0.5
MINIMUM_DAYS_FLOWER_APPEARS_EVEN_WITH_OPTIMAL_BIOMASS = 3

# FLOWER CLUSTERS - DRAWING
FLOWER_CLUSTER_LENGTH_AT_FULL_SIZE = 5
FLOWER_CLUSTER_LENGTH_AT_CREATION = 1
FLOWER_CLUSTER_ANGLE_WITH_STEM = 40
FLOWER_CLUSTER_SHAPE_ANGLE = 30
FLOWER_CLUSTER_SIDES = 3
RANDOM_FLOWER_CLUSTER_SWAY = 20
FLOWER_CLUSTER_SHAPE_PATTERN = "1234"
COLOR_FLOWER_CLUSTER = "#FFE303"
COLOR_FLOWER_CLUSTER_DEAD = 'b'# "#5E2605"

# -------------------------------------------------------------------------------------------
# FRUIT CLUSTERS
# -------------------------------------------------------------------------------------------

# FRUIT CLUSTERS - BIOMASS
START_FRUIT_CLUSTER_BIOMASS = 1
OPTIMAL_FRUIT_CLUSTER_BIOMASS = 8
BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY = 0.1
FRUIT_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW = 0.01

# FRUIT CLUSTERS - DRAWING
FRUIT_CLUSTER_LENGTH_AT_FULL_SIZE = 5
FRUIT_CLUSTER_LENGTH_AT_CREATION = 1
FRUIT_CLUSTER_ANGLE_WITH_STEM = 40
FRUIT_CLUSTER_SHAPE_ANGLE = 30
FRUIT_CLUSTER_SIDES = 2
RANDOM_FRUIT_CLUSTER_SWAY = 20
FRUIT_CLUSTER_SHAPE_PATTERN = "1232"
COLOR_FRUIT_CLUSTER = "#CD0000"
COLOR_FRUIT_CLUSTER_DEAD = 'b'#"#5E2605"

