import re
P1 = re.compile(r"^(?=(\w+\s?)+$).*")
P2 = re.compile(r"^((\w+\s?){7}){7}$")
