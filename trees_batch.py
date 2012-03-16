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

# This is just a little script that runs the tree simulator with a variety of species for testing.
# Because I saved time by making the parameters constants, I needed to feed in the species constant from outside.
# You wouldn't do this if you were reading the parameters from a data file.

import os

pythonLocation = "/Library/Frameworks/Python.framework/Versions/2.6/bin/python"

#ALL_SPECIES = ["Lift tree", "Spiral tree", "Bulb tree", 'Hobble tree', "Taproot tree", "Christmas tree"]
ALL_SPECIES = ["Taproot tree", "Christmas tree"]

for species in ALL_SPECIES:
	os.system('%s trees.py "%s"' % (pythonLocation, species))
