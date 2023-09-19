# Node Failure Detection 

The main objectives of this project was about implementing switch monitoring in a given ring topology.
Here, we are providing the outline of our approach to address the problem in question.
For a comprehensive description of the work and detailed results, please refer to the `Node_Failure_Detection.pptx` slide set file.

## Mininet Implementation

The initial phase involved constructing the necessary functions and executing them on a Mininet emulation. This served as an intermediary stage to ascertain the correct logic required for detecting switch failures. 
We opted for the most straightforward ring topology available, conveniently located in `/mininet-topologies/topology_1.py`.
You can find the outcome of this process in the script named `switch-monitor.py`.
Moreover, it's worth mentioning that we also tested this program on a mesh topology, found in `/mininet-topologies/topology_2.py`, and were successful.

## Lab Testbed Implementation

Upon gaining access to Lab BONSAI, the team conducted trials of the previous code on the larger ring topology of the Testbed. We discovered that the physical hardware did not respond in the same manner as the simulated switches. Consequently, certain adjustments were implemented to tailor the functions to the specific scenario. 
The fruits of this stage can be observed in the `switch-monitor-lab.py` script.

## DEMOs

The files labeled "DEMO" consist of videos demonstrating the projects running seamlessly without errors. 
Specifically, `Demo_lab.mp4` captures the project in action during a lab session, utilizing the lastes version of the code, as previously described.
`Demo_mininet.mp4` showcases the simulation of the smaller ring topology, utilizing again the 'switch-monitor-lab.py' program to demonstrate the script's successful functionality within the emulation environment.

### Running the codes

To execute the provided scripts and experience the functionalities described earlier, it's enough to run the mentioned files.
If one would also wish to test the hosts connectivity with the `hx ping hy` command, they should include the `my-first-app.py` code for both instances.

