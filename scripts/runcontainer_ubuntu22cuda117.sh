#!/usr/bin/env bash

# Run container from image
#IMAGE_ID="56e9b6fa7044"
IMAGE_name="myros2humble:latest" #"myros2triton:latest"
PLATFORM="$(uname -m)"
echo $PLATFORM

echo "Script executed from: ${PWD}"
BASEDIR=$(dirname $0)
echo "Script location: ${BASEDIR}"

#sudo xhost +si:localuser:root
# Map host's display socket to docker
DOCKER_ARGS+=("-v /tmp/.X11-unix:/tmp/.X11-unix")
DOCKER_ARGS+=("-e DISPLAY")
DOCKER_ARGS+=("-e NVIDIA_VISIBLE_DEVICES=all")
DOCKER_ARGS+=("-e NVIDIA_DRIVER_CAPABILITIES=all")
#DOCKER_ARGS+=("-e FASTRTPS_DEFAULT_PROFILES_FILE=/usr/local/share/middleware_profiles/rtps_udp_profile.xml")

# docker run --runtime nvidia --network host -it -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix \
#     $CONTAINER_NAME \
#     /bin/bash
docker run --runtime nvidia -it --rm \
    --privileged \
    --network host \
    ${DOCKER_ARGS[@]} \
    -v /dev/*:/dev/* \
	-v ${PWD}:/myROS2 \
    --runtime nvidia \
    --user="admin" \
    --workdir /myROS2 \
    $IMAGE_name \
    /bin/bash