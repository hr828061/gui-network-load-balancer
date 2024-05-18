import matplotlib.pyplot as plt

# Read data from the text file
data = []
with open('execution_times.txt', 'r') as file:
    for line in file:
        parts = line.strip().split(': ')
        print(parts)  # Print parts to see what's going wrong
        algo_name, servers, clients, runtime = parts[0], *map(float, parts[1].split(', '))
        data.append((algo_name, servers, clients, runtime))

# Separate data by algorithm
algo_data = {}
for entry in data:
    algo_name, servers, clients, runtime = entry
    if algo_name not in algo_data:
        algo_data[algo_name] = {'clients': [], 'runtimes': []}
    algo_data[algo_name]['clients'].append(clients)
    algo_data[algo_name]['runtimes'].append(runtime)

# Plotting
plt.figure(figsize=(10, 6))
for algo_name, data in algo_data.items():
    clients = data['clients']
    runtimes = data['runtimes']
    plt.plot(clients, runtimes, marker='o', linestyle='-', label=algo_name)

plt.title('Algorithm Runtimes vs. Number of Clients')
plt.xlabel('Number of Clients')
plt.ylabel('Runtime (seconds)')
plt.grid(True)
plt.legend()
plt.tight_layout()

# Show plot
plt.show()
