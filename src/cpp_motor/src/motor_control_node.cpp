
#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <vector>
#include <memory>

#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <cstring>
#include <cerrno>
#include <sys/ioctl.h>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"

using namespace std;
using std::placeholders::_1;
using namespace std::chrono_literals;

class DiffDriveSerialNode : public rclcpp::Node {
public:
    DiffDriveSerialNode() : Node("diff_drive_serial_node") {

        clock_ = this->get_clock();

        this->declare_parameter<std::string>("serial_port", "/dev/ttyAMA0");
        this->declare_parameter<double>("linear_scale", 400.0);  
        this->declare_parameter<double>("angular_scale", 200.0); 
        this->declare_parameter<double>("cmd_timeout_ms", 500.0); 
        this->declare_parameter<double>("loop_rate_hz", 20.0);   


        serial_port_ = this->get_parameter("serial_port").as_string();
        linear_scale_ = this->get_parameter("linear_scale").as_double();
        angular_scale_ = this->get_parameter("angular_scale").as_double();
        cmd_timeout_ms_ = this->get_parameter("cmd_timeout_ms").as_double();
        
        motor_polarities_ = {

        };


        if (!openAndConfigureSerial()) {
            RCLCPP_ERROR(this->get_logger(), "Failed to open serial port. Shutting down.");
            auto kill_timer = this->create_wall_timer(1ms, [this](){ rclcpp::shutdown(); });
            return;
        }


        sub_cmd_vel_ = this->create_subscription<geometry_msgs::msg::Twist>(
            "/cmd_vel",
            10,
            std::bind(&DiffDriveSerialNode::cmdVelCallback, this, _1)
        );


        double loop_period_ms = 1000.0 / this->get_parameter("loop_rate_hz").as_double();
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(static_cast<int>(loop_period_ms)),
            std::bind(&DiffDriveSerialNode::motorCommandLoop, this)
        );
        

        last_cmd_vel_time_ = clock_->now();


        rclcpp::on_shutdown(std::bind(&DiffDriveSerialNode::onShutdown, this));
        RCLCPP_INFO(this->get_logger(), "Diff Drive Serial Node initialized.");
        RCLCPP_INFO(this->get_logger(), "Listening on /cmd_vel. Sending to %s.", serial_port_.c_str());
    }

    ~DiffDriveSerialNode() {
        if (serial_fd_ >= 0) {
            RCLCPP_INFO(this->get_logger(), "Closing serial port.");
            close(serial_fd_);
        }
    }

private:
    bool openAndConfigureSerial() {
        serial_fd_ = open(serial_port_.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);
        if (serial_fd_ < 0) {
            RCLCPP_FATAL(this->get_logger(), "Error opening %s: %s", serial_port_.c_str(), strerror(errno));
            RCLCPP_FATAL(this->get_logger(), "Did you run with 'sudo'? Did you disable serial console in raspi-config?");
            return false;
        }
        

        int flags = fcntl(serial_fd_, F_GETFL, 0);
        flags &= ~O_NONBLOCK; 
        if (fcntl(serial_fd_, F_SETFL, flags) < 0) {
             RCLCPP_FATAL(this->get_logger(), "Error setting blocking mode: %s", strerror(errno));
             close(serial_fd_);
             return false;
        }

        struct termios tty;
        memset(&tty, 0, sizeof(tty));
        if (tcgetattr(serial_fd_, &tty) != 0) {
            RCLCPP_FATAL(this->get_logger(), "Error from tcgetattr: %s", strerror(errno));
            close(serial_fd_);
            return false;
        }

        cfsetospeed(&tty, B115200);
        cfsetispeed(&tty, B115200);

        tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;
        tty.c_cflag &= ~(PARENB | PARODD);
        tty.c_cflag &= ~CSTOPB;
        tty.c_cflag |= (CLOCAL | CREAD); 

        tty.c_lflag = 0; 
        tty.c_oflag = 0;
        tty.c_iflag = 0; 

        tty.c_iflag &= ~(IXON | IXOFF | IXANY);
        tty.c_cflag &= ~CRTSCTS;

        tty.c_cc[VMIN] = 0;  
        tty.c_cc[VTIME] = 0; 

        if (tcsetattr(serial_fd_, TCSANOW, &tty) != 0) {
            RCLCPP_FATAL(this->get_logger(), "Error from tcsetattr: %s", strerror(errno));
            close(serial_fd_);
            return false;
        }


        int status;
        if (ioctl(serial_fd_, TIOCMGET, &status) < 0) {
            RCLCPP_FATAL(this->get_logger(), "Error from TIOCMGET: %s", strerror(errno));
            close(serial_fd_);
            return false;
        }
        status &= ~TIOCM_RTS;
        status &= ~TIOCM_DTR;
        if (ioctl(serial_fd_, TIOCMSET, &status) < 0) {
            RCLCPP_FATAL(this->get_logger(), "Error from TIOCMSET: %s", strerror(errno));
            close(serial_fd_);
            return false;
        }
        
        // Flush any old data
        tcflush(serial_fd_, TCIOFLUSH);

        RCLCPP_INFO(this->get_logger(), "Port %s opened and configured.", serial_port_.c_str());
        return true;
    }


    void sendCommand(int id, int speed) {
        if (serial_fd_ < 0) return;

        string cmd = "{\"T\":10010,\"id\":" + to_string(id) + 
                     ",\"cmd\":" + to_string(speed) + ",\"act\":3}\n";
        
        ssize_t written = write(serial_fd_, cmd.c_str(), cmd.length());
        if (written < 0) {
            RCLCPP_WARN(this->get_logger(), "Error writing to serial port: %s", strerror(errno));
        } else if (static_cast<size_t>(written) < cmd.length()) {
            RCLCPP_WARN(this->get_logger(), "Incomplete write to serial port.");
        }
        
        std::this_thread::sleep_for(5ms);
    }


    void stopAllMotors() {
        if (serial_fd_ < 0) return;
        RCLCPP_INFO(this->get_logger(), "Sending stop command to all motors.");

        if (tcflush(serial_fd_, TCOFLUSH) < 0) {
             RCLCPP_WARN(this->get_logger(), "Error from tcflush: %s", strerror(errno));
        }

        for (int i = 0; i < 5; i++) {
            sendCommand(1, 0);
            sendCommand(2, 0);
            sendCommand(3, 0);
            sendCommand(4, 0);
            std::this_thread::sleep_for(50ms);
        }
    }


    void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg) {
        std::lock_guard<std::mutex> lock(cmd_mutex_);
        target_linear_x_ = msg->linear.x;
        target_angular_z_ = msg->angular.z;
        last_cmd_vel_time_ = clock_->now(); // Use the stored clock
    }


    void motorCommandLoop() {
        std::lock_guard<std::mutex> lock(cmd_mutex_);


        if ((clock_->now() - last_cmd_vel_time_).seconds() * 1000.0 > cmd_timeout_ms_) {
            if (target_linear_x_ != 0.0 || target_angular_z_ != 0.0) {
                RCLCPP_INFO(this->get_logger(), "Command timeout. Stopping motors.");
                target_linear_x_ = 0.0;
                target_angular_z_ = 0.0;
            }
        }

        double linear_rpm = target_linear_x_ * linear_scale_;
        double angular_rpm = target_angular_z_ * angular_scale_;

        int left_rpm = (int)(linear_rpm - angular_rpm);
        int right_rpm = (int)(linear_rpm + angular_rpm);

        int m1_speed = motor_polarities_[0] * left_rpm;
        int m2_speed = motor_polarities_[1] * right_rpm;
        int m3_speed = motor_polarities_[2] * left_rpm;
        int m4_speed = motor_polarities_[3] * right_rpm;


        sendCommand(1, m1_speed);
        sendCommand(2, m2_speed);
        sendCommand(3, m3_speed);
        sendCommand(4, m4_speed);

        RCLCPP_DEBUG(this->get_logger(), "Sent RPMs: L=%d, R=%d", left_rpm, right_rpm);
    }


    void onShutdown() {
        stopAllMotors();
        if (serial_fd_ >= 0) {
            close(serial_fd_);
            serial_fd_ = -1;
        }
        RCLCPP_INFO(this->get_logger(), "Shutdown complete.");
    }


    int serial_fd_ = -1;
    std::string serial_port_;
    double linear_scale_, angular_scale_, cmd_timeout_ms_;
    std::vector<int> motor_polarities_;


    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr sub_cmd_vel_;
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Clock::SharedPtr clock_; 


    std::mutex cmd_mutex_;
    double target_linear_x_ = 0.0;
    double target_angular_z_ = 0.0;
    rclcpp::Time last_cmd_vel_time_;
};


int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<DiffDriveSerialNode>();
    rclcpp::spin(node);
    return 0;
}

