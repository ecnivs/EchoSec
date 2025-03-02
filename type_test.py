while True:
    inn = input("-> ").lower()  # Convert input to lowercase for case insensitivity
    if any(word in inn for word in ("start", "run", "simul")) and any(word in inn for word in ("attack", "test", "simul")):
        print("YES")
        continue
    print("NO")


