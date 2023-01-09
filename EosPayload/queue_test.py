
import EosLib.packet.definitions
import EosLib.packet.packet
import EosLib.packet.transmit_header


def insert(list, n):

    index = len(list)
    # Searching for the position
    for i in range(len(list)):
        if list[i] > n:
            index = i
            break

    # Inserting n in the list
    if index == len(list):
        list = list[:index] + [n]
    else:
        list = list[:index] + [n] + list[index:]
    return list



if __name__ == "__main__":

    # array with packet priority (the array would be an array of packets not ints)
    arr = [0, 1, 1, 2, 2, 2, 10]

    # sample transmit
    arr.pop(0)

    # new packet comes in and gets inserted in array (the packet would be given from mqtt)
    arr = insert(arr, 3)

    # if there are elements in array then pop / transmit the packet
    # remember it may take a few hundred milliseconds for the packet to transmit
    arr.pop(0)
    arr.pop(0)
    arr.pop(0)

    print(arr)


