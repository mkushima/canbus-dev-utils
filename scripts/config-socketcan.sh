#!/bin/bash

################################################################################

#
# Print usage.
#
function print_usage()
{
    ME=$(basename "$0")

    cat << EOF

    Description:
        Configure the Socket CAN Bus

    Usage:
        ${ME} --up --interface 0 --bitrate 250000
        ${ME} --up --interface 1 --bitrate 500000
        ${ME} --up --interface 0 --virtual
        ${ME} --down --interface 0

    Options:
        -i|--interface       CAN Bus interface (0, 1, 2, ...)
        -b|--bitrate         CAN Bus bitrate (250000, 500000, ...)
        -db|--dbitrate       CAN Bus dbitrate for FD mode (1000000, 2000000, ...)
        --up                 Set CAN Bus UP
        --down               Set CAN Bus DOWN
        --fd                 FD mode
        --virtual            Set as virtual interface

    Note:
        Sudo rights is required.

EOF
}

################################################################################

#
# Parse command line
#
# params: Entire command line to parse (from script command line).
function parse_cmdline()
{
    while [[ $# -gt 0 ]]
    do
        key="$1"

        case $key in
            -h|--help)
                print_usage
                exit 0
            ;;

            -b|--bitrate) # (CAN bus bitrate)
                BITRATE="$2" # 250000, 500000
                shift  # past argument
            ;;
            
            -db|--dbitrate) # (CAN bus dbitrate - for CAN FD mode)
                DBITRATE="$2" # 1000000, 2000000
                shift  # past argument
            ;;

            -i|--interface) # (CAN bus interface)
                INTERFACE="can$2"  # 0, 1, 2, ...
                shift  # past argument
            ;;

            --up) # (Set CAN bus UP)
                UP="true"
            ;;

            --down) # (Set CAN bus DOWN)
                DOWN="true"
            ;;
            
            --fd) # (Set CAN bus FD mode)
                FD="true"
            ;;

            --virtual) # (Set CAN bus as virtual interface)
                VIRTUAL="true"
            ;;

            *)
                echo "Unknown parameter: ${key}"
                echo "See usage:"
                print_usage
                exit 2
            ;;
        esac

        shift  # past argument or value
    done

    if [[ "$VIRTUAL" = "true" ]]; then
        if [[ "$UP" == "true" ]]; then
            do_action=bring_vcan_up
        else # Assume that user has choosen only UP or DOWN action (it will be validate by sanity check)
            do_action=bring_vcan_down
        fi
    else
        if [[ "$UP" == "true" ]]; then
            do_action=bring_can_up
        else # Assume that user has choosen only UP or DOWN action (it will be validate by sanity check)
            do_action=bring_can_down
        fi
    fi
}

################################################################################

#
# Command line sanity check
#
function cmdline_sanity_check()
{
    if [[ "$UP" == "true" && "$DOWN" == "true" ]]; then
        echo "Please, choose JUST ONE action: UP or DOWN"
        print_usage
        exit 1
    fi

    if [[ "$UP" == "" && "$DOWN" == "" ]]; then
        echo "No action has been selected. Please, choose one: --up or --down"
        print_usage
        exit 1
    fi

    if [[ "$INTERFACE" == "" ]]; then
        echo "Please, provide an interface to configure the Socket CAN"
        print_usage
        exit 1
    fi

    if [[ "$UP" == "true" ]] && [[ "$BITRATE" == "" && "$VIRTUAL" != "true" ]]; then
        echo "Please, provide a bitrate for bringing the Socket CAN up"
        print_usage
        exit 1
    fi
    
    if [[ "$UP" == "true" ]] && [[ "$FD" == "true" ]] && [[ "$DBITRATE" == "" && "$VIRTUAL" != "true" ]]; then
        echo "FD mode is set, please, provide dbitrate for bringing the Socket CAN up"
        print_usage
        exit 1
    fi
}

################################################################################

function bring_can_up()
{
    bring_can_down
    
    echo "Bring $INTERFACE up at $BITRATE bps"
    
    if [[ "$FD" == "true" ]]; then
        sudo ip link set $INTERFACE type can bitrate $BITRATE sample-point 0.8 dbitrate $DBITRATE dsample-point 0.7 fd on
    else
        sudo ip link set $INTERFACE type can bitrate $BITRATE
    fi

    sudo ip link set up $INTERFACE
}

################################################################################

function bring_can_down()
{
    echo "Bring $INTERFACE down"

    sudo ip link set down $INTERFACE
}

################################################################################

function bring_vcan_up()
{
    bring_vcan_down
    
    echo "Bring v$INTERFACE up"

    sudo ip link add dev v$INTERFACE type vcan
    
    if [[ "$FD" == "true" ]]; then
        sudo ip link set v$INTERFACE mtu 72
    fi

    sudo ip link set up v$INTERFACE
}

################################################################################

function bring_vcan_down()
{
    echo "Bring v$INTERFACE down"

    sudo ip link set down v$INTERFACE
    sudo ip link delete dev v$INTERFACE
}

################################################################################

main()
{
    parse_cmdline "$@"
    
    cmdline_sanity_check

    "$do_action"
}

main "$@"
