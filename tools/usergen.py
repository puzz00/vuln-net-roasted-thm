#!/usr/bin/python3

# a program to generate common username possibilities
# for bruteforcing kerberos to reveal usernames
# by puzz00

def add_colon(n):
    return n.replace(" ", ":")

def add_dot(n):
    return n.replace(" ", ".")

def add_hyphen(n):
    return n.replace(" ", "-")

def add_underscore(n):
    return n.replace(" ", "_")

def initial_first(n):
    i = n.find(" ")
    return n[0] + n[i:]

def initial_first_spaceless(n):
    i = n.find(" ")
    return n[0] + n[i+1:]

def initial_last(n):
    i = n.find(" ")
    return n[:i+1] + n[i+1]

def initial_last_spaceless(n):
    i = n.find(" ")
    return n[:i] + n[i+1]

def remove_space(n):
    return n.replace(" ", "")

def three(n):
    i = n.find(" ")
    j = n[:i]
    k = n[i+1:]
    if len(j) >= 3 and len(k) >= 3:
        return n[:3] + n[i:i+4]
    elif len(j) >=3:
        return n[:3] + n[i:]
    elif len(k) >= 3:
        return n[:i] + n[i:i+4]
    else:
        return n

def three_spaceless(n):
    i = n.find(" ")
    return n[:i] + n[i+1:]

# load initial usernames from a txt file
with open("users.txt", "r") as file:
    users = []
    for line in file:
        line = line.strip()
        users.append(line)

# mangle the usernames
users_1 = [add_colon(n) for n in users]
users_2 = [remove_space(n) for n in users]
users_3 = [add_dot(n) for n in users]
users_4 = [add_hyphen(n) for n in users]
users_5 = [add_underscore(n) for n in users]
users_6 = [initial_first(n) for n in users]
users_7 = [initial_first_spaceless(n) for n in users]
users_8 = [add_colon(n) for n in users_6]
users_9 = [add_dot(n) for n in users_6]
users_10 = [add_hyphen(n) for n in users_6]
users_11 = [add_underscore(n) for n in users_6]
users_12 = [initial_last(n) for n in users]
users_13 = [initial_last_spaceless(n) for n in users]
users_14 = [add_colon(n) for n in users_12]
users_15 = [add_dot(n) for n in users_12]
users_16 = [add_hyphen(n) for n in users_12]
users_17 = [add_underscore(n) for n in users_12]
users_18 = [three(n) for n in users]
users_19 = [three_spaceless(n) for n in users_18]
users_20 = [add_colon(n) for n in users_18]
users_21 = [add_dot(n) for n in users_18]
users_22 = [add_hyphen(n) for n in users_18]
users_23 = [add_underscore(n) for n in users_18]

# create a final user list
final_users = users + users_1 + users_2 + users_3 + users_4 + users_5
final_users += users_6 + users_7 + users_8 + users_9 + users_10 + users_11
final_users += users_12 + users_13 + users_14 + users_15 + users_16 + users_17
final_users += users_18 + users_19 + users_20 + users_21 + users_22 + users_23

# output a txt file using the final user list
with open(r"mangled_users.txt", "w") as file:
    for name in final_users:
        file.write(f"{name}\n")
