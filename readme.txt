TerasologyTrees is a proof-of-concept tree growth simulator I wrote for possible inclusion in the open source sandbox game Terasology.
For more details see http://www.woodspeople.net/terasology/terasology_model_description.html. 

Due to limited time, I wrote the simulation in Python, the language I know best and can work fastest in. 
Then, to get to drawing trees quickly, I grabbed hold of the matplotlib Python graphics library and 
just threw the plant into a 3D scatterplot to see it. To make this work in Terasology the code will have 
to be translated to Java and integrated. It is not a huge amount of code, and I don't think this is an 
insurmountable task for the enthusiastic :) but I can't say.

To play with the simulation in Python, you need to set up python with numpy and matplotlib on top of it, 
then check out the code from the GitHub repository. The simulation is very simple: it just spits out PNG 
files with tree pictures on them, as well as a description file with details on growth. You can change the 
parameters and create new "species" simply by manipulating the trees_parameters.py file.

