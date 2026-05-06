# ─────────────────────────────────────────────
#  CPU Scheduling Simulator
# ─────────────────────────────────────────────

def get_int(prompt, *, min_val=None, max_val=None):
    """Keep asking until the user enters a valid integer within optional bounds."""
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(f"  Value must be ≥ {min_val}\n")
            elif max_val is not None and value > max_val:
                print(f"  Value must be ≤ {max_val}\n")
            else:
                return value
        except ValueError:
            print("  Input must be an integer\n")


def print_gantt(gantt, time_marks):
    """Print a Gantt chart with time marks aligned under every block border."""
    W = 6  # width of each block (including the '|' separator)

    # De-duplicate adjacent identical marks before printing
    marks = [time_marks[0]]
    for t in time_marks[1:]:
        if t != marks[-1]:
            marks.append(t)

    print("\nGantt Chart:")

    # ── process row ──────────────────────────────
    print("|", end="")
    for label in gantt:
        print(f"{str(label):^{W - 1}}|", end="")
    print()

    # ── timeline row ─────────────────────────────
    # Each mark sits at the left edge of its block boundary.
    # marks[0] is under the opening '|' (position 0).
    # marks[k] is under the '|' after block k, i.e. at position k * W.
    # We track how many characters we've already printed so each
    # mark is right-padded to land exactly on the next boundary.

    printed = 0  # characters printed so far on the timeline row
    for k, t in enumerate(marks):
        target = k * W          # character position this mark belongs at
        pad    = target - printed
        label  = str(t)
        print(" " * pad + label, end="")
        printed = target + len(label)

    print("\n")


def print_table(title, processes, arrival, burst, waiting, turnaround, priority=None):
    """Print the scheduling results table and averages."""
    n = len(processes)
    header = "Process\tAT\tBT\t" + ("PR\t" if priority else "") + "WT\tTAT"
    print(f"\n{title}:")
    print(header)
    for i in range(n):
        pr_col = f"{priority[i]}\t" if priority else ""
        print(f"{processes[i]}\t{arrival[i]}\t{burst[i]}\t{pr_col}{waiting[i]}\t{turnaround[i]}")

    print(f"\nAverage Waiting Time:    {sum(waiting)  / n:.2f}")
    print(f"Average Turnaround Time: {sum(turnaround) / n:.2f}")


# ── data collection ───────────────────────────

def collect_data(need_priority=False, need_quantum=False):
    """
    Gather process data from the user and return a dict with:
      processes, arrival, burst, priority (optional), quantum (optional)
    """
    while True:
        n = get_int("How many processes?: ", min_val=3)

        processes, arrival, burst, priority = [], [], [], []

        for k in range(n):
            pid = f"P{k + 1}"
            processes.append(pid)
            burst.append(get_int(f"\nEnter Burst Time for {pid}: ", min_val=0))

            if need_priority:
                # Arrival time is skipped for non-preemptive priority (all arrive at 0)
                arrival.append(get_int(f"Enter Arrival Time for {pid}: ", min_val=0))
                pv = get_int(
                    f"Enter Priority Value for {pid} (1–{n}): ",
                    min_val=0, max_val=n
                )
                priority.append(pv)
                print()
            else:
                arrival.append(get_int(f"Enter Arrival Time for {pid}: ", min_val=0))

        quantum = None
        if need_quantum:
            quantum = get_int("Enter time quantum (≥ 2): ", min_val=2)

        return {
            "processes": processes,
            "arrival": arrival,
            "burst": burst,
            "priority": priority if need_priority else None,
            "quantum": quantum,
        }


def collect_data_no_arrival(need_priority=False):
    """Variant that sets all arrival times to 0 (used by non-preemptive priority)."""
    while True:
        n = get_int("How many processes?: ", min_val=3)

        processes, arrival, burst, priority = [], [], [], []

        for k in range(n):
            pid = f"P{k + 1}"
            processes.append(pid)
            burst.append(get_int(f"\nEnter Burst Time for {pid}: ", min_val=0))
            arrival.append(0)  # fixed

            if need_priority:
                pv = get_int(
                    f"Enter Priority Value for {pid} (1–{n}): ",
                    min_val=0, max_val=n
                )
                priority.append(pv)
                print()

        return {
            "processes": processes,
            "arrival": arrival,
            "burst": burst,
            "priority": priority if need_priority else None,
            "quantum": None,
        }


# ── scheduling algorithms ─────────────────────

def fcfs():
    """First Come, First Serve (non-preemptive)."""
    d = collect_data()
    processes, arrival, burst = d["processes"], d["arrival"], d["burst"]
    n = len(processes)

    wt  = [0] * n
    tat = [0] * n

    order        = sorted(range(n), key=lambda i: arrival[i])
    current_time = 0
    gantt        = []
    marks        = [0]

    for i in order:
        if current_time < arrival[i]:          # CPU idle gap
            gantt.append("Idle")
            marks.append(arrival[i])
            current_time = arrival[i]

        wt[i]  = current_time - arrival[i]
        tat[i] = wt[i] + burst[i]

        gantt.append(processes[i])
        current_time += burst[i]
        marks.append(current_time)

    print_table("First Come, First Serve", processes, arrival, burst, wt, tat)
    print_gantt(gantt, marks)


def sjf():
    """Shortest Job First (non-preemptive)."""
    d = collect_data()
    processes, arrival, burst = d["processes"], d["arrival"], d["burst"]
    n = len(processes)

    wt   = [0] * n
    tat  = [0] * n
    ct   = [0] * n
    done = [False] * n

    current_time = 0
    gantt        = []
    marks        = [0]

    while not all(done):
        available = [i for i in range(n) if arrival[i] <= current_time and not done[i]]

        if not available:                      # CPU idle
            gantt.append("Idle")
            marks.append(current_time)
            current_time += 1
            continue

        idx = min(available, key=lambda x: burst[x])
        gantt.append(processes[idx])
        marks.append(current_time)

        current_time   += burst[idx]
        ct[idx]         = current_time
        tat[idx]        = ct[idx] - arrival[idx]
        wt[idx]         = tat[idx] - burst[idx]
        done[idx]       = True

    marks.append(current_time)
    print_table("Shortest Job First (SJF)", processes, arrival, burst, wt, tat)
    print_gantt(gantt, marks)


def srtf():
    """Shortest Remaining Time First (preemptive SJF)."""
    d = collect_data()
    processes, arrival, burst = d["processes"], d["arrival"], d["burst"]
    n = len(processes)

    remaining    = burst[:]
    wt           = [0] * n
    tat          = [0] * n
    ct           = [0] * n
    current_time = 0
    completed    = 0
    last         = -1

    gantt = []
    marks = [0]

    while completed < n:
        available = [i for i in range(n) if arrival[i] <= current_time and remaining[i] > 0]

        if not available:
            if last != -1:
                gantt.append("Idle")
                marks.append(current_time)
                last = -1
            current_time += 1
            continue

        idx = min(available, key=lambda x: remaining[x])

        if last != idx:
            gantt.append(processes[idx])
            marks.append(current_time)
            last = idx

        remaining[idx] -= 1
        current_time   += 1

        if remaining[idx] == 0:
            ct[idx]   = current_time
            tat[idx]  = ct[idx] - arrival[idx]
            wt[idx]   = tat[idx] - burst[idx]
            completed += 1

    marks.append(current_time)
    print_table("Shortest Remaining Time (SRT)", processes, arrival, burst, wt, tat)
    print_gantt(gantt, marks)


def rr():
    """Round Robin."""
    d = collect_data(need_quantum=True)
    processes, arrival, burst, quantum = d["processes"], d["arrival"], d["burst"], d["quantum"]
    n = len(processes)

    remaining    = burst[:]
    ct           = [0] * n
    wt           = [0] * n
    tat          = [0] * n
    visited      = [False] * n
    queue        = []
    current_time = 0
    completed    = 0

    gantt = []
    marks = [0]

    def enqueue_arrivals(up_to_time):
        """Add any processes that have arrived by up_to_time and haven't been visited."""
        new = sorted(
            [i for i in range(n) if arrival[i] <= up_to_time and not visited[i]],
            key=lambda x: arrival[x]
        )
        for i in new:
            queue.append(i)
            visited[i] = True

    enqueue_arrivals(0)

    while completed < n:
        if not queue:                          # CPU idle: jump to next arrival
            next_t = min(arrival[i] for i in range(n) if not visited[i])
            gantt.append("Idle")
            marks.append(next_t)
            current_time = next_t
            enqueue_arrivals(current_time)
            continue

        i        = queue.pop(0)
        run      = min(quantum, remaining[i])
        gantt.append(processes[i])
        current_time  += run
        remaining[i]  -= run
        marks.append(current_time)

        enqueue_arrivals(current_time)         # arrivals during this slice

        if remaining[i] > 0:
            queue.append(i)
        else:
            completed   += 1
            ct[i]        = current_time
            tat[i]       = ct[i] - arrival[i]
            wt[i]        = tat[i] - burst[i]

    print_table("Round Robin", processes, arrival, burst, wt, tat)
    print_gantt(gantt, marks)


# ── priority scheduling ───────────────────────

def _ps_non_preemptive(processes, arrival, burst, priority):
    """Non-preemptive priority (all arrive at t=0)."""
    n    = len(processes)
    wt   = [0] * n
    tat  = [0] * n
    ct   = [0] * n
    done = [False] * n

    current_time = 0
    gantt        = []
    marks        = [0]

    while not all(done):
        available = [i for i in range(n) if arrival[i] <= current_time and not done[i]]

        if not available:
            next_t = min(arrival[i] for i in range(n) if not done[i])
            gantt.append("Idle")
            marks.append(next_t)
            current_time = next_t
            continue

        idx = min(available, key=lambda x: (priority[x], arrival[x]))
        gantt.append(processes[idx])
        current_time += burst[idx]
        ct[idx]   = current_time
        tat[idx]  = ct[idx] - arrival[idx]
        wt[idx]   = tat[idx] - burst[idx]
        done[idx] = True
        marks.append(current_time)

    return wt, tat, gantt, marks


def _ps_preemptive(processes, arrival, burst, priority):
    """Preemptive priority."""
    n         = len(processes)
    remaining = burst[:]
    wt        = [0] * n
    tat       = [0] * n
    ct        = [0] * n

    current_time = 0
    completed    = 0
    prev         = None

    gantt = []
    marks = [0]

    while completed < n:
        available = [i for i in range(n) if arrival[i] <= current_time and remaining[i] > 0]

        if not available:
            if prev != "Idle":
                gantt.append("Idle")
                if marks[-1] != current_time:
                    marks.append(current_time)
                prev = "Idle"
            current_time += 1
            continue

        idx = min(available, key=lambda x: (priority[x], arrival[x]))

        if prev != idx:
            gantt.append(processes[idx])
            if marks[-1] != current_time:
                marks.append(current_time)
            prev = idx

        remaining[idx] -= 1
        current_time   += 1

        if remaining[idx] == 0:
            completed += 1
            ct[idx]    = current_time
            tat[idx]   = ct[idx] - arrival[idx]
            wt[idx]    = tat[idx] - burst[idx]

    marks.append(current_time)
    return wt, tat, gantt, marks


def _ps_round_robin(processes, arrival, burst, priority, quantum):
    """Priority + Round Robin."""
    n         = len(processes)
    remaining = burst[:]
    wt        = [0] * n
    tat       = [0] * n
    ct        = [0] * n

    rr_queues = {}          # priority_value -> [process indices]
    in_queue  = [False] * n
    current_time = 0
    completed    = 0

    gantt = []
    marks = [0]

    def enqueue(up_to):
        for i in range(n):
            if arrival[i] <= up_to and remaining[i] > 0 and not in_queue[i]:
                rr_queues.setdefault(priority[i], []).append(i)
                in_queue[i] = True

    enqueue(0)

    while completed < n:
        active = [p for p in rr_queues if rr_queues[p]]

        if not active:                         # CPU idle
            next_t = min(arrival[i] for i in range(n) if remaining[i] > 0)
            current_time = next_t
            enqueue(current_time)
            continue

        best = min(active)
        idx  = rr_queues[best].pop(0)

        run = min(quantum, remaining[idx])
        gantt.append(processes[idx])
        if marks[-1] != current_time:
            marks.append(current_time)

        current_time   += run
        remaining[idx] -= run

        enqueue(current_time)                  # arrivals during this slice

        if remaining[idx] > 0:
            rr_queues[best].append(idx)
        else:
            completed   += 1
            ct[idx]      = current_time
            tat[idx]     = ct[idx] - arrival[idx]
            wt[idx]      = tat[idx] - burst[idx]
            in_queue[idx] = False

    marks.append(current_time)
    return wt, tat, gantt, marks


def ps():
    """Priority Scheduling menu."""
    MENU = {
        1: ("Non-Preemptive Priority", False, False),
        2: ("Preemptive Priority",     True,  False),
        3: ("Priority + Round Robin",  True,  True),
    }

    while True:
        print()
        for k, (label, *_) in MENU.items():
            print(f"{k}. {label}")

        choice = get_int("Select: ", min_val=1, max_val=3)
        title, needs_arrival, needs_quantum = MENU[choice]

        if choice == 1:
            d = collect_data_no_arrival(need_priority=True)
        else:
            d = collect_data(need_priority=True, need_quantum=needs_quantum)

        processes = d["processes"]
        arrival   = d["arrival"]
        burst     = d["burst"]
        priority  = d["priority"]
        quantum   = d["quantum"]

        if choice == 1:
            wt, tat, gantt, marks = _ps_non_preemptive(processes, arrival, burst, priority)
        elif choice == 2:
            wt, tat, gantt, marks = _ps_preemptive(processes, arrival, burst, priority)
        else:
            wt, tat, gantt, marks = _ps_round_robin(processes, arrival, burst, priority, quantum)

        print_table(title, processes, arrival, burst, wt, tat, priority=priority)
        print_gantt(gantt, marks)
        break


# ── main ─────────────────────────────────────

def main():
    MENU = {
        1: ("First Come, First Serve", fcfs),
        2: ("Shortest Job First",      sjf),
        3: ("Shortest Remaining Time", srtf),
        4: ("Round Robin",             rr),
        5: ("Priority Scheduling",     ps),
    }

    while True:
        print()
        for k, (label, _) in MENU.items():
            print(f"{k}.) {label}")
        print(f"{len(MENU) + 1}.) Exit")

        choice = get_int("Select a CPU Scheduling Algorithm: ", min_val=1, max_val=len(MENU) + 1)

        if choice == len(MENU) + 1:
            break
        elif choice in MENU:
            MENU[choice][1]()
        else:
            print("\nInvalid choice\n")


if __name__ == "__main__":
    main()