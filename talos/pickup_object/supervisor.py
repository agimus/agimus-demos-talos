# Theses variables are defined:
# - robot, a SoT device
# - simulateTorqueFeedbackForEndEffector, a boolean

import sys
if not hasattr(sys, "argv"):
    sys.argv = []

def hpTasks(sotrobot):
    from sot_hpp.tools import COM, Foot, Manifold
    com = COM ("talos", sotrobot)
    lf = Foot ("talos/leg_left_6_joint", sotrobot) # Feet placement make the robot fall down.
    rf = Foot ("talos/leg_right_6_joint", sotrobot)
    return com + lf + rf

def makeSupervisorWithFactory (robot):
    from sot_hpp import Supervisor
    from sot_hpp.factory import Factory, Affordance
    from sot_hpp.tools import Manifold
    from sot_hpp.srdf_parser import parse_srdf
    from hpp.corbaserver.manipulation import Rule

    grippers = [ "talos/left_gripper", "table/pose" ]
    objects = [ "box" ]
    handlesPerObjects = [ [ "box/handle1", "box/handle2", "box/pose1", "box/pose2" ], ]
    rules = [ Rule([ "table/pose", ], [ "box/handle[12]", ], False),
              Rule([ "talos/left_gripper", ], [ "box/pose[12]", ], False),
              Rule([ "table/pose", ], [ "box/pose1", ], False),
              Rule([ "talos/left_gripper", ], [ Object.handles[1], ], False),
              Rule([ "talos/left_gripper", ], [ Object.handles[0], ], True),
              # Rule([ "talos/right_gripper", ], [ Object.handles[1], ], True),
              Rule([ "table/pose", ], [ "box/pose2", ], True),
              ]

    srdf = {}
    srdfTalos = parse_srdf ("srdf/talos.srdf", packageName = "talos_data", prefix="talos")
    srdfBox   = parse_srdf ("srdf/cobblestone.srdf", packageName = "gerard_bauzil", prefix="box")
    srdfTable = parse_srdf ("srdf/pedestal_table.srdf", packageName = "gerard_bauzil", prefix="table")
    for w in [ "grippers", "handles" ]:
        srdf[w] = dict()
        for d in [ srdfTalos, srdfBox ]:
            srdf[w].update (d[w])

    supervisor = Supervisor (robot, hpTasks = hpTasks(robot))
    factory = Factory(supervisor)
    factory.parameters["period"] = rospy.get_param("/sot_controller/dt")
    factory.parameters["simulateTorqueFeedback"] = simulateTorqueFeedbackForEndEffector
    factory.parameters["addTracerToAdmittanceController"] = True
    # factory.parameters["addTimerToSotControl"] = True
    factory.setGrippers (grippers)
    factory.setObjects (objects, handlesPerObjects, [ [] for e in objects ])
    factory.setRules (rules)
    factory.setupFrames (srdf["grippers"], srdf["handles"], robot)
    factory.addAffordance (
        Affordance ("talos/left_gripper", "box/handle1",
            openControlType="position_torque", closeControlType="position_torque",
            refs = { "angle_open": (0,), "angle_close": (-0.5,), "torque": (-5.,) },
            simuParams = { "refPos": (-0.2,) }))
    factory.generate ()

    supervisor.makeInitialSot ()
    return supervisor

# Set initial config
robot.device.set (tuple([-0.74,] + list(robot.device.state.value[1:])))
supervisor = makeSupervisorWithFactory (robot)

from dynamic_graph_hpp.sot import RosQueuedSubscribe
re = RosQueuedSubscribe ('ros_export')

supervisor.plugTopics(re)
supervisor.setupEvents ()
supervisor.plugSot("")