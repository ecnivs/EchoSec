import colorama
from settings import *
from colorama import Fore, Style, Back

# Initialize colorama
colorama.init(autoreset=True)

class CliUI:
    """CLI-based user interface with colored output for assistant responses and user input."""

    def __init__(self, assistant_name: str, handler):
        self.assistant_name = assistant_name
        self.handler = handler
        self.user_color = Fore.CYAN
        self.assistant_color = Fore.GREEN
        self.highlight_color = Fore.YELLOW
        self.prompt_color = Fore.MAGENTA
        self.status_color = Fore.BLUE
        self.error_color = Fore.RED
        self.recording_status = False
        self.status_thread = None
        self.stop_status = threading.Event()
        self.running = True

        # Start the static score bar in a separate thread
        self.score_thread = threading.Thread(target=self.update_score_bar, daemon=True)
        self.score_thread.start()

    def clear_screen(self):
        """Clear the terminal screen."""
        print("\033[H\033[J", end="")

    def print_header(self):
        """Print a stylish header for the assistant."""
        header_width = len(self.assistant_name) + 20
        print(f"{Back.BLACK}{Fore.WHITE}{Style.BRIGHT}╔{'═' * header_width}╗")
        print(f"║{' ' * 10}{self.assistant_name}{' ' * 10}║")
        print(f"╚{'═' * header_width}╝{Style.RESET_ALL}")
        print()

    def print_help_text(self):
        print(f"{Fore.BLUE}{Style.BRIGHT}{HELP_TEXT}{Style.RESET_ALL}")
        print()

    def print_assistant_response(self, text):
        """Print the assistant's response in the assistant color."""
        words = str(text).split()
        lines = []
        current_line = []

        for word in words:
            if len(' '.join(current_line + [word])) > 80:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        print(f"{self.assistant_color}{self.assistant_name} >{Style.RESET_ALL}", end=" ")

        for i, line in enumerate(lines):
            if i > 0:
                print(f"{' ' * (len(self.assistant_name) + 3)}", end="")
            print(f"{self.assistant_color}{line}{Style.RESET_ALL}")
            if i < len(lines) - 1:
                print()
        print()

    def print_user_input(self, text: str):
        """Print the user's input in the user color."""
        print(f"{self.user_color}You > {text}{Style.RESET_ALL}\n")

    def update_score_bar(self):
        """Continuously updates the static score bar at the bottom of the screen with score and level."""
        while self.running:
            if self.handler.sim:
                sys.stdout.write(
                    f"\r{Fore.YELLOW}Score: {self.handler.score} | High Score: {self.handler.high_score} | Level: {self.handler.level} {Style.RESET_ALL}"
                )
            sys.stdout.flush()
            time.sleep(0.5)

    def stop(self):
        """Stop the UI threads."""
        self.running = False
        self.score_thread.join()

    def show_error(self, message: str):
        """Show an error message."""
        print(f"{self.error_color}Error: {message}{Style.RESET_ALL}")

