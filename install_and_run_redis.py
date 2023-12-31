import subprocess


def install_and_run_redis():
    try:
        # Install Redis using the package manager
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "redis-server", "-y"])

        # Start the Redis server
        subprocess.Popen(["redis-server"])
        print("Redis server installed and started")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    install_and_run_redis()
