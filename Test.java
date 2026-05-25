package org.firstinspires.ftc.teamcode.pedroPathing.main.motor;

public class Test {
    public static void main(String[] args) {
        // (x1, y1) is the robot's current position (any metric system can be used, as long as it's consistent)
        double x1 = 56; 
        double y1 = 20;
        double x2 = 15;
        double y2 = 128;

        double robotAngle = Math.toRadians(180); // robot angle must be -180 degrees to 180 degrees

        double atan2 = Math.atan2(y2 - y1, x2 - x1);
        // double rad = (atan2 - robotAngle + 2 * Math.PI) % (2 * Math.PI);
        double rad = atan2 - robotAngle;
        rad = (rad > Math.PI) ? rad - 2 * Math.PI : rad;
        double angle = Math.toDegrees(rad);
        double dist = Math.hypot(x2-x1, y2-y1);

        System.out.println(angle);
        System.out.println(dist);
    }
}