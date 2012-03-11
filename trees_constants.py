# -----------------------------------------------------------------------------------------------------------------
# proof-of-concept dynamic object oriented tree generator 
# for terasology project
# written by cynthia kurtz
# -----------------------------------------------------------------------------------------------------------------

INDENT = '---->'
DIRECTIONS = ["north", "east", "south", "west", "up", "down"]

SIZE_OF_SPACE_XY = 100
SIZE_OF_SPACE_Z = 300
GROUND_LEVEL = 100

PATCHY_SUN = True

PATCHY_WATER = True
NUM_WATER_PATCHES = 50
WATER_PATCH_RADIUS = 2

PATCHY_MINERALS = True
NUM_MINERAL_PATCHES = 50
MINERAL_PATCH_RADIUS = 2

DRAW_ROOTS = True
DRAW_STEMS = True
DRAW_LEAF_CLUSTERS = True
DRAW_MERISTEMS = True
DRAW_FLOWER_CLUSTERS = True
DRAW_FRUIT_CLUSTERS = True

NUM_BLOCKS_ABOVE_FOR_MAX_SHADE_STRESS = 10

BIOMASS_DISTRIBUTION_SPREAD = {}
BIOMASS_DISTRIBUTION_ORDER = {}
MIN_STRESS_TO_TRIGGER_BIOMASS_REDISTRIBUTION = 0.3

# normal growth favors leaves and growing stems
BIOMASS_DISTRIBUTION_SPREAD["no stress"] = [0.4, 0.4]
BIOMASS_DISTRIBUTION_ORDER["no stress"] = [
	["leaves", "child", "branches", "root", "axillary meristems", "apical meristems", "flowers", "fruits", ],
	["axillary meristems", "apical meristems", "branches", "child", "above-ground tree",],
	]

# in low light or shade conditions, the plant shunts biomass to meristems so new stems can develop and reach for the light
# root biomass distribution is unaffected
BIOMASS_DISTRIBUTION_SPREAD["low sun or shade"] = [0.7, 0.4]
BIOMASS_DISTRIBUTION_ORDER["low sun or shade"] = [
	["child", "apical meristems", "axillary meristems", "leaves", "branches", "root", "flowers", "fruits", ],
	["axillary meristems", "apical meristems", "branches", "child", "above-ground tree",],
	]

# in conditions of water or mineral stress, biomass is shunted down to the roots so they can grow
# to find more water and/or minerals
BIOMASS_DISTRIBUTION_SPREAD["water or mineral stress"] = [0.7, 0.7]
BIOMASS_DISTRIBUTION_ORDER["water or mineral stress"] = [
	["root", "parent", "child", "branches", "axillary meristems", "apical meristems", "leaves", "fruits", "flowers", ],
	["child", "apical meristems", "axillary meristems", "branches",  "above-ground tree",],
	]

# when the plant enters reproductive mode, everything moves to the flowers, then fruits
# even extra biomass in the roots is pulled up to be used for reproduction
BIOMASS_DISTRIBUTION_SPREAD["reproduction"] = [0.7, 0.7]
BIOMASS_DISTRIBUTION_ORDER["reproduction"] = [
	["flowers", "fruits", "child", "branches", "leaves", "axillary meristems", "apical meristems", "root", ],
	["above-ground tree", "parent", "child", "apical meristems", "axillary meristems", "branches", ],
	]

# the distribution of water and minerals is the same in all conditions, because it is dependent on the
# workings of the xylem and phloem
WATER_DISTRIBUTION_SPREAD_PERCENT = [0.4, 0.6]
WATER_DISTRIBUTION_ORDER = [["leaves", "child", 'branches'], ["above-ground tree", 'parent'],]

MINERALS_DISTRIBUTION_SPREAD_PERCENT = [0.4, 0.6]
MINERALS_DISTRIBUTION_ORDER = [["leaves", "child", 'branches'],["above-ground tree", 'parent'],]

