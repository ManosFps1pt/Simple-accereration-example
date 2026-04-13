```java


package org.firstinspires.ftc.teamcode.pedroPathing.main.subsystem;

import static org.firstinspires.ftc.robotcore.external.BlocksOpModeCompanion.telemetry;

import com.bylazar.configurables.annotations.Configurable;
import com.bylazar.telemetry.PanelsTelemetry;
import com.bylazar.telemetry.TelemetryManager;
import com.pedropathing.geometry.Pose;
import com.pedropathing.math.Vector;
import com.qualcomm.hardware.limelightvision.LLResult;
import com.qualcomm.robotcore.hardware.HardwareMap;

import org.firstinspires.ftc.teamcode.pedroPathing.main.constants.RobotConstants;
import org.firstinspires.ftc.teamcode.pedroPathing.main.motor.MotorConfig;
import org.firstinspires.ftc.teamcode.pedroPathing.main.motor.MotorMode;

@Configurable
public class Turret {
    static double maxPower = .5, kp=0.005, kd = .001, ki=0, ks=0, manualMaxPower = .2, ramp = 1;
    public static double movingShotLeadFactor = 1.0;
    HardwareMap hwmap;
    TelemetryManager telemetryM = PanelsTelemetry.INSTANCE.getTelemetry();
    MotorConfig turret = RobotConstants.TURRET_CONFIG;
    final Pose RED_GOAL_POSE = new Pose(144, 144);
    final Pose BLUE_GOAL_POSE = new Pose(0, 144);
    public Turret(HardwareMap hwmap) {
        this.hwmap = hwmap;
    }
    double angleToGoal;
    public void faceForward() {
        turret.setPositionInRadians(0);
    }
    public void setAngleRadians(double angleRadians) {
        turret.setPositionInRadians(angleRadians);
        turret.setMotorMode(MotorMode.PROFILED_PIDF);
    }
    public double getAngleToGoal(){
        return angleToGoal;
    }
    public void lookToGoal(Pose pose, boolean isRed) {
        double atan2;
        if (isRed) {
            atan2 = Math.atan2(RED_GOAL_POSE.getY()-pose.getY(), RED_GOAL_POSE.getX()-pose.getX());
        } else {
            atan2 = Math.atan2(BLUE_GOAL_POSE.getY()-pose.getY(), BLUE_GOAL_POSE.getX()-pose.getX());
        }
        // robot angle must be -180 degrees to 180 degrees
        double rad = (atan2 - pose.getHeading());
        rad = (rad > Math.PI) ? rad - 2 * Math.PI : rad;
        angleToGoal = rad;
        setAngleRadians(angleToGoal);
        turret.setMotorMode(MotorMode.PROFILED_PIDF);
        telemetryM.addData("angle to goal", angleToGoal);
        telemetryM.addData("rad", rad);
        telemetryM.addData("atan2", rad);
    }

    public void lookToGoalWhileMoving(Pose pose, Vector velocity, boolean isRed) {
        lookToGoalWhileMoving(pose, velocity, movingShotLeadFactor, isRed);
    }

    public void lookToGoalWhileMoving(Pose pose, Vector velocity, double leadFactor, boolean isRed) {
        if (pose == null || velocity == null) return;

        /*
         * Aiming at (goal + a * velocity) is equivalent to aiming from
         * (pose - a * velocity), which lets us reuse the existing lookToGoal() path.
         */
        Pose compensatedPose = new Pose(
                pose.getX() - leadFactor * velocity.getXComponent(),
                pose.getY() - leadFactor * velocity.getYComponent(),
                pose.getHeading()
        );

        lookToGoal(compensatedPose, isRed);
        telemetryM.addData("moving shot lead factor", leadFactor);
        telemetryM.addData("moving shot vx", velocity.getXComponent());
        telemetryM.addData("moving shot vy", velocity.getYComponent());
    }
    public void init() {
        turret.init(hwmap);
        faceForward();
    }
    public void limelightAim(LLResult result) {
        turret.maxPower = maxPower;
        turret.kP = kp; turret.kD = kd; turret.kI = ki; turret.kS = ks;
        if (result != null) {
            if (result.isValid()) {
                telemetryM.addLine("valid result");
                if (result.getTx() == 0) {
                    turret.manualPositionPIDF(0);
                    telemetryM.addLine("0 power");
                }
                else {
                    turret.manualPositionPIDF(-result.getTx());
                    telemetryM.addLine("running turret");
                }
            }
            else {
                turret.manualPositionPIDF(0);
                telemetryM.addLine("invalid result");
            }
        }
        else {
            telemetryM.addLine("null result");
        }
        telemetryM.addData("kp", turret.kP);
        telemetryM.addData("kd", turret.kD);
        telemetryM.addData("tx", result.getTx());
        telemetryM.addData("max power", turret.maxPower);
        telemetryM.addData("power", turret.getPower());
    }
    public void manualControl(double input) {
        turret.extraPower = manualMaxPower * input;
        telemetryM.addData("turret extra power", turret.extraPower);
    }
    public void loop() {
        turret.maxPower = maxPower;
        turret.update();
        telemetryM.addData("turret mode", turret.getMotorMode());
        telemetryM.addData("power", turret.getPower());
        telemetryM.addData("velocity", turret.getVelocity());
        telemetryM.addData("ref vel", turret.getvRef());
        telemetryM.addData("position", turret.getCurrentPosition());
        telemetryM.addData("min pos", turret.getMinAngleTicks());
        telemetryM.addData("max pos", turret.getMaxAngleTicks());
        telemetryM.addData("ref pos", turret.getxRef());
        telemetryM.addData("ref a", turret.getaRef());
        telemetryM.addData("current", turret.getCurrent());
        telemetryM.addData("ks motor", turret.kS);
        telemetryM.addData("target", turret.getTargetPositionTicks());
    }
}

```

```java

package org.firstinspires.ftc.teamcode.pedroPathing.main.motor.math.controllers;


import androidx.annotation.NonNull;

import com.qualcomm.robotcore.util.Range;

import org.firstinspires.ftc.teamcode.pedroPathing.main.motor.MotionState;
import org.firstinspires.ftc.teamcode.pedroPathing.main.motor.coefficients.MotionProfilingCoefficients;
import org.firstinspires.ftc.teamcode.pedroPathing.main.motor.math.units.Angle;
import org.firstinspires.ftc.teamcode.pedroPathing.main.motor.math.units.AngularVelocity;

public class TrapezoidalMotionProfileController implements MotorController{
    private final MotionProfilingCoefficients coef;
    private final PIDFFPositionController pidFFController;
    private Angle xRef = Angle.fromRadians(0);
    private AngularVelocity vRef = AngularVelocity.fromRadPerSec(0);
    private double aRef = 0.0; // rad/s^2

    public TrapezoidalMotionProfileController(MotionProfilingCoefficients coefficients) {
        this.coef = coefficients;
        pidFFController = new PIDFFPositionController(coef.getPidCoef());
    }

    @Override
    public double update(MotionState target, @NonNull MotionState motionState, double dt) {
        return update(target, motionState, dt, 1.0);
    }

    public double update(MotionState target,
                         @NonNull MotionState motionState,
                         double dt,
                         double feedforwardScale) {
        if (dt == 0.0) {
            throw new ArithmeticException("dt cannot be zero");
        }

        double position = motionState.getPosition().toRadians();
        double velocity = motionState.getVelocity().toRadPerSec();

        double targetRad = target.getPosition().toRadians();
        double xRefRad = xRef.toRadians();
        double vRefRad = vRef.toRadPerSec();

        double remaining = targetRad - xRefRad;

        double stoppingDistance =
                (vRefRad * vRefRad) / (2.0 * coef.getMaxAcceleration());

        if (Math.signum(vRefRad) == Math.signum(remaining) &&
                Math.abs(remaining) <= stoppingDistance) {
            aRef = -Math.signum(velocity) * coef.getMaxAcceleration();
        } else {
            aRef = Math.signum(remaining) *coef.getMaxAcceleration();
        }
        vRefRad += aRef * dt;
        vRefRad = Range.clip(vRefRad,
                -coef.getMaxVelocity(),
                coef.getMaxVelocity());

        xRefRad += vRefRad * dt;

        if (Math.signum(targetRad - xRefRad) != Math.signum(remaining)) {
            xRefRad = targetRad;
            vRefRad = 0.0;
            aRef = 0.0;
        }

        xRef = Angle.fromRadians(xRefRad);
        vRef = AngularVelocity.fromRadPerSec(vRefRad);
        MotionState refState = new MotionState(xRef, vRef, aRef);
        double staticFeedforwardSign = Math.signum(vRefRad);
        if (staticFeedforwardSign == 0.0) {
            staticFeedforwardSign = Math.signum(targetRad - position);
        }
        return pidFFController.update(
                refState,
                motionState,
                dt,
                feedforwardScale,
                staticFeedforwardSign
        );
    }

    public MotionState getReferenceState() {
        return new MotionState(xRef, vRef, aRef);
    }

    public void reset(MotionState measuredState) {
        xRef = measuredState.getPosition();
        vRef = measuredState.getVelocity();
        aRef = measuredState.getAcceleration();
        pidFFController.reset();
    }

    @Override
    public void reset() {
        reset(new MotionState(
                Angle.fromRadians(0.0),
                AngularVelocity.fromRadPerSec(0.0),
                0.0
        ));
    }
}

```
