surnames = ['first', 'second', 'third']
for pos, sur in enumerate(surnames):
	print(pos, sur)

#enumerate
people = ['Tom','Mike','John']
ages = ['35','25','28']
for position, value in enumerate(people):
	print(people[position], ages[position])

#zip
for person, age in zip(people, ages):
	print(person, age)