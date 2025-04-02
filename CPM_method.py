import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import networkx as nx
import matplotlib.pyplot as plt
import csv


class CPMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Metoda CPM")
        self.root.geometry("600x400")

        # Tabela do wprowadzania danych
        self.tree = ttk.Treeview(root, columns=("Zadanie", "Czas", "Poprzednicy"), show="headings")
        self.tree.heading("Zadanie", text="Zadanie")
        self.tree.heading("Czas", text="Czas trwania")
        self.tree.heading("Poprzednicy", text="Poprzednicy")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Przyciski
        frame_buttons = tk.Frame(root)
        frame_buttons.pack(pady=5)

        tk.Button(frame_buttons, text="Dodaj zadanie", command=self.add_task).grid(row=0, column=0, padx=5)
        tk.Button(frame_buttons, text="Usuń zadanie", command=self.delete_task).grid(row=0, column=1, padx=5)
        tk.Button(frame_buttons, text="Oblicz CPM", command=self.calculate_cpm).grid(row=0, column=2, padx=5)
        tk.Button(frame_buttons, text="Zapisz do CSV", command=self.save_to_csv).grid(row=0, column=3, padx=5)
        tk.Button(frame_buttons, text="Wczytaj CSV", command=self.load_from_csv).grid(row=0, column=4, padx=5)
        tk.Button(frame_buttons, text="Reset", command=self.reset_app).grid(row=0, column=5, padx=5)

    def add_task(self):
        new_window = tk.Toplevel(self.root)
        new_window.title("Dodaj zadanie")

        tk.Label(new_window, text="Nazwa:").pack()
        entry_name = tk.Entry(new_window)
        entry_name.pack()

        tk.Label(new_window, text="Czas trwania:").pack()
        entry_time = tk.Entry(new_window)
        entry_time.pack()

        tk.Label(new_window, text="Poprzednicy (oddzielone przecinkami):").pack()
        entry_prev = tk.Entry(new_window)
        entry_prev.pack()

        def save_task():
            task_name = entry_name.get().strip()
            task_time = entry_time.get().strip()
            task_prev = entry_prev.get().strip()

            if not task_name:
                messagebox.showerror("Błąd", "Nazwa zadania nie może być pusta.")
                return
            if not task_time.isdigit():
                messagebox.showerror("Błąd", "Czas trwania musi być liczbą całkowitą.")
                return

            self.tree.insert("", "end", values=(task_name, int(task_time), task_prev))
            new_window.destroy()

        btn_save = tk.Button(new_window, text="Dodaj", command=save_task)
        btn_save.pack()

    def delete_task(self):
        """Usuwa zaznaczone zadanie z tabeli"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Brak wyboru", "Zaznacz zadanie do usunięcia.")
            return

        confirm = messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć zaznaczone zadanie?")
        if confirm:
            for item in selected_item:
                self.tree.delete(item)

    def reset_app(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        messagebox.showinfo("Reset", "Wszystkie zadania zostały usunięte.")

    def calculate_cpm(self):
        tasks = []
        for row in self.tree.get_children():
            task, duration, predecessors = self.tree.item(row)["values"]
            tasks.append((task, int(duration), predecessors.split(",")))

        G = nx.DiGraph()
        durations = {}
        for task, duration, predecessors in tasks:
            G.add_node(task)
            durations[task] = duration
            for pred in predecessors:
                if pred.strip():
                    G.add_edge(pred.strip(), task)

        ES = {task: 0 for task in G.nodes}
        EF = {task: 0 for task in G.nodes}

        for task in nx.topological_sort(G):
            if G.in_edges(task):
                ES[task] = max(EF[pred] for pred, _ in G.in_edges(task))
            EF[task] = ES[task] + durations[task]

        project_duration = max(EF.values())
        LF = {task: project_duration for task in G.nodes}
        LS = {task: project_duration for task in G.nodes}

        for task in reversed(list(nx.topological_sort(G))):
            if G.out_edges(task):
                LF[task] = min(LS[next_task] for _, next_task in G.out_edges(task))
            LS[task] = LF[task] - durations[task]

        R = {task: LS[task] - ES[task] for task in G.nodes}
        critical_path = [task for task in G.nodes if R[task] == 0]

        result_window = tk.Toplevel(self.root)
        result_window.title("Wyniki CPM")

        result_tree = ttk.Treeview(result_window, columns=("Zadanie", "ES", "EF", "LS", "LF", "R"), show="headings")
        result_tree.heading("Zadanie", text="Zadanie")
        result_tree.heading("ES", text="Najwcześniejszy start (ES)")
        result_tree.heading("EF", text="Najwcześniejsze zakończenie (EF)")
        result_tree.heading("LS", text="Najpóźniejszy start (LS)")
        result_tree.heading("LF", text="Najpóźniejsze zakończenie (LF)")
        result_tree.heading("R", text="Rezerwa (R)")
        result_tree.pack(fill=tk.BOTH, expand=True)

        for task in G.nodes:
            result_tree.insert("", "end", values=(task, ES[task], EF[task], LS[task], LF[task], R[task]))

        tk.Label(result_window, text=f"Ścieżka krytyczna: {' -> '.join(critical_path)}",
                 font=("Arial", 12, "bold")).pack(pady=5)

        self.draw_cpm_graph(G, critical_path)

    def draw_cpm_graph(self, G, critical_path):
        plt.figure(figsize=(12, 7))
        pos = nx.spring_layout(G, seed=42)

        node_colors = ['red' if task in critical_path else 'skyblue' for task in G.nodes]

        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, alpha=0.9)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
        nx.draw_networkx_edges(G, pos, edge_color='gray', width=2, arrows=True, connectionstyle="arc3,rad=0.1")

        edge_labels = {(u, v): '' for u, v in G.edges}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='gray')

        plt.title("Diagram CPM – Czerwone węzły oznaczają ścieżkę krytyczną", fontsize=14)
        red_patch = plt.Line2D([0], [0], marker='o', color='w', label='Ścieżka krytyczna',
                               markerfacecolor='red', markersize=10)
        blue_patch = plt.Line2D([0], [0], marker='o', color='w', label='Pozostałe zadania',
                                markerfacecolor='skyblue', markersize=10)
        plt.legend(handles=[red_patch, blue_patch], loc='upper left')

        plt.axis('off')
        plt.tight_layout()
        plt.show()

    def save_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Zadanie", "Czas", "Poprzednicy"])
            for row in self.tree.get_children():
                writer.writerow(self.tree.item(row)["values"])

        messagebox.showinfo("Sukces", "Dane zostały zapisane do pliku CSV")

    def load_from_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        with open(file_path, mode="r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                self.tree.insert("", "end", values=row)

        messagebox.showinfo("Sukces", "Dane zostały wczytane z pliku CSV")


if __name__ == "__main__":
    root = tk.Tk()
    app = CPMApp(root)
    root.mainloop()
