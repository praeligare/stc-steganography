import math
import random
import numpy as np
import matplotlib.pyplot as plt
from bitstring import BitArray
from PIL import Image
from ete3 import Tree

cover_index = 0
message_index = 0
y = []
cover = []
path = ''
stego_img = None
show_img = True
tree = None

def reset_global_vars(sub_height):
    global cover_index, message_index, y, tree, stego_img
    cover_index = 0
    message_index = 0
    y = []
    tree = init_trellis(sub_height)
    stego_img = []

def get_user_input():
    output = "Would you like to\n"
    output += "    (1) choose a message to hide\n"
    output += "    (2) generate random messages and see graphical representations of their embedding efficiencies\n"
    output += "    (3) generate random submatrix of different size and see graphical representations of their distortions\n"
    output += "    (4) generate random submatrix of same size and see graphical representations of their efficiencies\n"
    output += "    (5) look for the optimal choice of submatrix\n"
    while True:
        option = input(output)
        if (not (option == '1' or option == '2' or option == '3' or option == '4' or option == '5')):
            print("Unrecognized input. Try again.")
        else:
            return option

def arbitrary_payload():
    global cover, h, sub_height, sub_width, message
    cover = select_img()
    sub_h = get_sub_h()
    print("Submatrix currently fixed at\n", np.asarray(sub_h))
    sub_height = len(sub_h)
    sub_width = len(sub_h[0])

    message = get_user_message(sub_width)
    print("Generating matrix H...\n")
    h = get_h(sub_h, len(message), len(cover))
    print("H = \n" + str(h))

    reset_global_vars(sub_height)
    embed(message, sub_width)
    extract(h)

    distortion = calculate_distortion(Image.open(path).convert('L'), stego_img)
    print("Distortion:", distortion)
    print("Message length:", len(message))
    print("Result in efficiency:", get_efficiency(len(message), distortion))

def random_payload_efficiencies():
    global cover, h, sub_height, sub_width, message, show_img
    show_img = False
    cover = select_img(13)
    
    sub_h = get_sub_h()
    print("Submatrix currently fixed at\n", np.asarray(sub_h))
    sub_height = len(sub_h)
    sub_width = len(sub_h[0])

    message_number = 30
    abscissa = []
    ordinate = []
    for inverse_alpha in range(10, 20 + 2, 2):
        print("1 / alpha = ", inverse_alpha)
        alpha = 1 / inverse_alpha
        message_length = math.floor(len(cover) * alpha) 
        messages = get_random_payloads(message_number, message_length)
        h = get_h(sub_h, len(messages[0]), len(cover))
        efficiencies = []
        for i in range(message_number):
            print("    message", i, "/", message_number)
            message = messages[i]
            
            reset_global_vars(sub_height)
            embed(message, sub_width)

            distortion = calculate_distortion(Image.open(path).convert('L'), stego_img)
            efficiencies.append(get_efficiency(message_length, distortion))
            print("Message length = ", message_length, ", distortion = ", distortion, ", efficiency = ", efficiencies[i])
        abscissa.append(inverse_alpha)
        ordinate.append(np.median(np.asarray(efficiencies)))
    generate_graph("For n = " + str(len(cover)) + " sub_width = " + str(sub_width) + " sub_height = " + str(sub_height), abscissa, ordinate, "1 / alpha", "efficiency")

def random_submatrix_distortions():
    global cover, h, sub_height, sub_width, message, show_img
    cover = select_img(13)
    show_img = False
    sizes = np.asarray([(2, 2), (3, 5), (4, 7), (6, 7)])
    sub_hs = []
    print("Generating submatrix")
    for s in sizes:
        sub_hs.append(get_random_sub_h(s[0], s[1]))
    abscissa = []
    ordinate = []
    alpha = 0.1
    message_length = math.floor(len(cover) * alpha)
    message = get_random_payloads(1, message_length)[0]
    for i in range(len(sub_hs)):
        print("Submatrix", i, "/", len(sub_hs))
        sub_h = sub_hs[i]
        sub_height = len(sub_h)
        sub_width = len(sub_h[0])
        print("Generating H")
        h = get_h(sub_h, len(message), len(cover))

        reset_global_vars(sub_height)
        embed(message, sub_width)

        distortion = calculate_distortion(Image.open(path).convert('L'), stego_img)
        abscissa.append(i + 1)
        ordinate.append(distortion)

    x_label = "sizes: "
    for i in range(len(sizes)):
        x_label += "(" + str(sizes[i][0]) + "x" + str(sizes[i][1]) + ")"
        if(i != len(sizes) - 1):
            x_label += ", "

    generate_graph("For n = " + str(len(cover)) + ", alpha = " + str(alpha), abscissa, ordinate, x_label, "distortion")

def random_submatrix_efficiencies():
    global cover, h, sub_height, sub_width, message, show_img
    cover = select_img(13)
    show_img = False
    sub_height = strict_integer_input("\nSubmatrix height: ")
    sub_width = strict_integer_input("Submatrix width: ")
    sub_hs = []
    submatrix_number = 100
    print("Generating submatrix")
    for i in range(submatrix_number):
        sub_hs.append(get_random_sub_h(sub_height, sub_width))
    abscissa = []
    ordinate = []
    alpha = 0.1
    message_length = math.floor(len(cover) * alpha)
    message = get_random_payloads(1, message_length)[0]
    for i in range(len(sub_hs)):
        print("submatrix", i, "/", len(sub_hs))
        sub_h = sub_hs[i]
        print("Generating H")
        h = get_h(sub_h, len(message), len(cover))

        reset_global_vars(sub_height)
        embed(message, sub_width)

        distortion = calculate_distortion(Image.open(path).convert('L'), stego_img)
        efficiency = get_efficiency(message_length, distortion)
        abscissa.append(i + 1)
        ordinate.append(efficiency)
    ordinate = -np.sort(-np.asarray(ordinate))
    generate_graph("For n = " + str(len(cover)) + ", alpha = " + str(alpha), abscissa, ordinate, "random submatrix sorted by efficiency", "efficiency")

def get_optimal_submatrix():
    global cover, h, sub_height, sub_width, message, show_img
    cover = select_img(13)
    show_img = False
    sub_height = strict_integer_input("\nSubmatrix height: ")
    sub_width = strict_integer_input("Submatrix width: ")
    sub_hs = []
    submatrix_number = 100
    print("Generating submatrix")
    for i in range(submatrix_number):
        sub_hs.append(get_random_sub_h(sub_height, sub_width))
    efficiencies = []
    alpha = 0.1
    message_length = math.floor(len(cover) * alpha)
    message = get_random_payloads(1, message_length)[0]
    for i in range(len(sub_hs)):
        print("submatrix", i, "/", len(sub_hs))
        sub_h = sub_hs[i]
        print("Generating H")
        h = get_h(sub_h, len(message), len(cover))

        reset_global_vars(sub_height)
        embed(message, sub_width)

        distortion = calculate_distortion(Image.open(path).convert('L'), stego_img)
        efficiency = get_efficiency(message_length, distortion)
        efficiencies.append(efficiency)
    print("Best submatrix found:\n", sub_hs[np.argmax(efficiencies)])


def get_user_message(sub_width):

    def txt_to_bin(str):
        txt_bits = []
        dico = {}
        for i in range(256):
            dico[chr(i)] = i
        w = ""
        for c in str:
            p = w + c
            if(dico.get(p) != None):
                w = p
            else:
                dico[p] = len(dico)
                txt_bits.append(dico[w])
                w = c
        txt_bits.append(dico[w])
        message = np.empty(len(txt_bits) * 12, 'uint8')
        for i in range(len(txt_bits)):
            str_bits = format(txt_bits[i], '012b')
            for j in range(len(str_bits)):
                message[i * 12 + j] = str_bits[j]
        return message

    while True:
        txt_input = input("What would you like to hide today? ")
        bin_input = txt_to_bin(txt_input)
        if len(bin_input) > len(cover):
            print("\nThis message is too large for the selected cover! Try something shorter.")
        else:
            #size = len(cover)//sub_width
            #str(bin_input).ljust(size - len(bin_input), '0')
            return bin_input

def get_random_payloads(message_number, message_length):
    return np.random.randint(0, 2, (message_number, message_length))

def strict_integer_input(output):
    while True:
        value = input(output + ' ')
        if (not value.strip().isdigit()):
                print("\nIntegers only, please.")
        else:
            break
    return int(value)

def strict_binary_input(output):
    while True:
        value = input(output + ' ').strip()
        non_binary = None
        for character in value:
            if (not (character == '0' or character == '1')):
                non_binary = True
                break
        if (non_binary or len(value) == 0):
            print("\nBase 2 numbers only, please.\n")
        else:
            break
    return int(value)

def select_img(cover_number = None):
    global path
    if(cover_number == None):
        while True:
            cover_number = strict_integer_input("\nSelect image as cover [1-13]:")
            if (cover_number > 13):
                print("\nUp to 13 only!")
            else:
                break
    path = '../img/' + str(cover_number) + '.pgm'
    img_bits = img_to_lsb(path)
    print("Cover: " + str(img_bits) + '\n')
    return img_bits

def img_to_lsb(path):
    img = Image.open(path).convert('L')
    return  np.mod(np.asarray(img), 2).flatten()

def get_random_sub_h(sub_height, sub_width):
    sub_h = np.random.randint(0, 2, (sub_height, sub_width), "uint8")
    if(not np.isin(1, sub_h[0])):
        sub_h[0][np.random.randint(sub_width)] = 1
    if(not np.isin(1, sub_h[sub_height - 1])):
        sub_h[sub_height - 1][np.random.randint(sub_width)] = 1
    return sub_h

def get_efficiency(message_length, distortion):
    if(distortion == 0):
        return message_length / 0.1
    return message_length / distortion

def get_sub_h():
    sub_h = []
    sub_height = strict_integer_input("\nSubmatrix height: ")
    sub_width = strict_integer_input("Submatrix width: ")

    while True:
            option = input("Would you like to\n    (1) generate a randomized submatrix\n    (2) manually input a submatrix\n")
            if (not (option == '1' or option == '2')):
                print("Unrecognized input. Try again.")
            else:
                break
    match option:
        case '1':
            print("Generating submatrix...\n")
            sub_h = get_random_sub_h(sub_height, sub_width)
        case '2':
            print("We're now building the submatrix, element by element.\n")

            for row in range(sub_height):
                sub_h.append([])
                for column in range(sub_width):
                    sub_h[row].append(strict_binary_input(f'Enter binary number for row {row}, column {column}: '))
            print("Inputs done!\n")
    return sub_h

def get_h(sub_h, payload_size, message_size):

    sub_height = len(sub_h)
    sub_width = len(sub_h[0])
    h_width = message_size
    h_height = payload_size
    h = np.zeros((h_height, h_width), dtype='int8')

    def place_submatrix(h_row, h_column):
        for row in range(sub_height):
            for column in range(sub_width):
                if (h_row + row < h_height and h_column + column < h_width):
                    h[h_row + row][h_column + column] = sub_h[row][column]

    for row in range(h_height):
        for column in range(h_width):
            if (column == row * sub_width):
                place_submatrix(row, column)

    return h

def init_trellis(sub_height):
    tree = Tree()
    root = tree.get_tree_root()
    root.add_features(y_bit='-')
    first_node = tree.add_child(name='s' + ''.zfill(sub_height) + 'p0')
    first_node.add_features(dist=0, weight=0, state=''.zfill(sub_height), level='p0', y_bit='-')
    return tree

def get_column(h, sub_width, sub_height):
    global cover_index
    column = ''
    offset = int(cover_index/sub_width)
    for row in range(offset, offset + sub_height):
        if (row == len(h)):
            break
        column = column + str(h[row][cover_index])
    return column[::-1].zfill(sub_height)

def add_edge(tree, node, y_bit):
    global cover_index
    cost = cover[cover_index] ^ y_bit
    weight = node.weight + cost

    match y_bit:
        case 0:
            next_state = node.state
        case 1:
            column = get_column(h, sub_width, sub_height)
            next_state = str(bin(int(node.state, 2) ^ int(column, 2))[2:]).zfill(sub_height)

    existing_node = tree.search_nodes(state=next_state, level=cover_index+1)

    if (len(existing_node)):
        existing_node = existing_node[0]
        if (existing_node.weight > weight):
            existing_node.detach()
            node.add_child(existing_node)
            existing_node.add_features(dist=cost, weight=weight, y_bit=y_bit)
    else:
        new_node = node.add_child(name='s' + str(next_state) + 'c' + str(cover_index+1), dist=cost)
        new_node.add_features(weight=weight, y_bit=y_bit, state=next_state, level=cover_index+1)

def move_inside_block(sub_width, tree):
    global cover_index
    for i in range(sub_width):
        if i == 0:
            level = 'p' + str(message_index)
        else:
            level = cover_index
        column_nodes = tree.search_nodes(level=level)
        for node in column_nodes:
            add_edge(tree, node, 0)
            add_edge(tree, node, 1)
        cover_index += 1
    exit_block()

def exit_block():
    global cover_index, message_index, y, tree
    column_nodes = tree.search_nodes(level=cover_index)

    for node in column_nodes:
        if node.state[-1] == str(message[message_index]):
            connect_blocks(node)

def connect_blocks(node):
    global message_index, tree
    next_state = '0' + node.state[:-1]
    existing_node = tree.search_nodes(state=next_state, level=node.level+1)

    if (len(existing_node)):
        existing_node = existing_node[0]
        if (existing_node.weight > node.weight):
            existing_node.detach()
            node.add_child(existing_node)
            existing_node.add_features(weight=node.weight)
    else:
        new_node = node.add_child(dist=0, name='s' + next_state + 'p' + str(message_index+1))
        new_node.add_features(state=next_state, level='p'+str(message_index+1), weight=node.weight, y_bit='-')

        # check if last block
        if(message_index == len(message) - 1):
            get_y(new_node)

def embed(message, sub_width):
    global message_index
    for index in range(len(message)):
        message_index = index
        move_inside_block(sub_width, tree)

def get_y(node):
    global y
    while node:
        if (isinstance(node.y_bit, int)):
            y.insert(0, node.y_bit)
        node = node.up

    for i in range(len(y), len(cover)):
        y.append(cover[i])

    print("\nCalculating stego object done.")
    if(show_img):
        print("Opening both images...")
    display_imgs()

def display_imgs():
    global stego_img

    img = Image.open(path).convert('L')
    img_pixels = np.asarray(img, 'uint8')

    def get_stego_pixels():
        global path, cover
        stego_pixels = []
        difference = []
        difference = np.absolute(y - cover)
        difference_matrix = vector_to_matrix(difference)

        for i in range(len(img_pixels)):
            stego_pixels.append([])
            for j in range(len(img_pixels[0])):
                stego_pixels[i].append(img_pixels[i][j] + difference_matrix[i][j])
                # Instead of adding 1, we decrement the maximum (255) by 1
                if(stego_pixels[i][j] == 256):
                    stego_pixels[i][j] = 254
        return np.asarray(stego_pixels, 'uint8')

    def vector_to_matrix(vector):
        matrix = []
        cover_rows = len(img_pixels)
        cover_columns = len(img_pixels[0])
        for i in range(cover_rows):
            matrix.append([])
            for j in range(cover_columns):
                matrix[i].append(vector[i * cover_rows + j])
        return matrix

    cover_img = Image.fromarray(img_pixels, 'L')
    if(show_img):
        cover_img.show(title="Cover image")
    stego_pixels = get_stego_pixels()
    stego_img = Image.fromarray(stego_pixels, 'L')
    if(show_img):
        stego_img.show(title="Stego image")

def extract(h):

    def bin_to_txt(message):
        str = ""
        dico = {}
        for i in range(256):
            dico[i] = chr(i)
        txt_bits = packed(message)
        v = txt_bits[0]
        w = dico[v]
        str += w
        for i in range(1, len(txt_bits)):
            v = txt_bits[i]
            if(dico.get(v) != None):
                entry = dico[v]
            else:
                entry = w + w[0]
            str += entry
            dico[len(dico)] = w + entry[0]
            w = entry
        return str

    def packed(message):
        txt_bits = []
        for i in range(0, len(message), 12):
            txt_bits.append(int(''.join(np.array(message, '<U1')[i:i+12]), 2))
        return txt_bits

    m = np.matmul(h, np.mod(np.asarray(stego_img),2).flatten())
    for i in range(len(m)):
        m[i] %= 2

    txt_output = bin_to_txt(list(m))

    print("\nMessage retrieved.")
    print("M = " + txt_output + '\n')

def generate_graph(title, x, y, x_label, y_label):
    plt.plot(x,y)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.show()

def calculate_distortion(cover_img, stego_img):
    return np.absolute(np.asarray(cover_img, np.int16).flatten() - np.asarray(stego_img, np.int16).flatten()).sum()

if __name__ == '__main__':

    print("\nHello! Welcome to our approach to PLS embedding using Syndrome-Trellis Coding.")
    print("We hope this command-line finds you well.\n")

    option = get_user_input()

    match(option):
        case '1':
            arbitrary_payload()
        case '2':
            random_payload_efficiencies()
        case '3':
            random_submatrix_distortions()
        case '4':
            random_submatrix_efficiencies()
        case '5':
            get_optimal_submatrix()
