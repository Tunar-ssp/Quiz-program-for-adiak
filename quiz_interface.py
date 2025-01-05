import tkinter as tk
from tkinter import ttk, messagebox
import random
import os

def read_answers():
    answers = {}
    try:
        with open('anw.txt', 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and '|' in line and not line.endswith('|'):
                    try:
                        num, ans = line.split('|')
                        if num.strip().isdigit():
                            answers[int(num)] = ans.strip().upper()
                    except ValueError:
                        continue
    except FileNotFoundError:
        messagebox.showerror("Xəta", "anw.txt faylı tapılmadı!")
        return None
    except Exception as e:
        messagebox.showerror("Xəta", f"Faylı oxuyarkən problem yarandı: {str(e)}")
        return None
    
    if not answers:
        messagebox.showerror("Xəta", "Cavablar faylı boşdur!")
        return None
        
    return answers

def read_questions():
    questions = {}
    try:
        # Əvvəlcə .docx faylını yoxlayaq
        if os.path.exists('questions.docx'):
            from docx import Document
            doc = Document('questions.docx')
            current_question = ""
            current_number = None
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    if text[0].isdigit():
                        if current_number and current_question:
                            questions[current_number] = current_question
                        
                        number = ''
                        for char in text:
                            if char.isdigit():
                                number += char
                            elif number:
                                break
                        
                        if number:
                            current_number = int(number)
                            question_text = text[text.find(')') + 1:] if ')' in text else text[len(number):]
                            current_question = question_text.strip()
                    else:
                        if current_question:
                            current_question += " " + text
            
            if current_number and current_question:
                questions[current_number] = current_question
                
        # Əgər .docx faylı yoxdursa, .txt faylını yoxlayaq
        elif os.path.exists('questions.txt'):
            with open('questions.txt', 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            number, question = line.split(';', 1)
                            questions[int(number.strip())] = question.strip()
                        except ValueError:
                            continue
        else:
            messagebox.showerror("Xəta", "Nə questions.docx, nə də questions.txt faylı tapılmadı!")
            return None
            
    except Exception as e:
        messagebox.showerror("Xəta", f"Sualları oxuyarkən problem yarandı: {str(e)}")
        return None
    
    if not questions:
        messagebox.showerror("Xəta", "Suallar faylı boşdur!")
        return None
        
    return questions

def format_question(question_text):
    """Sualı və variantları formatla"""
    # Əvvəldəki nöqtəni sil
    if question_text.startswith('.'):
        question_text = question_text[1:].strip()
        
    # Sual və variantları ayır
    parts = question_text.split('A)')
    if len(parts) != 2:
        return question_text
        
    question = parts[0].strip()
    options = 'A)' + parts[1].strip()
    
    # Variantları ayır və formatla
    options = options.replace('A)', '\nA) ')
    options = options.replace('B)', '\nB) ')
    options = options.replace('C)', '\nC) ')
    options = options.replace('D)', '\nD) ')
    options = options.replace('E)', '\nE) ')
    
    return f"{question}\n{options}"

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Proqramı")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Dəyişənlər
        self.questions = read_questions()
        self.answers = read_answers()
        
        if not self.questions or not self.answers:
            self.root.quit()
            return
            
        self.used_questions = set()
        self.current_question = None
        self.correct_count = 0
        self.total_attempted = 0
        self.wrong_questions = []
        
        # Ana konteyner
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sual bölməsi
        self.question_frame = ttk.LabelFrame(self.main_frame, text="Sual", padding="10")
        self.question_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.question_text = tk.Text(self.question_frame, wrap=tk.WORD, height=10,
                                   font=('Arial', 12), bg='white')
        self.question_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Cavab bölməsi
        self.answer_frame = ttk.Frame(self.main_frame)
        self.answer_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.answer_var = tk.StringVar()
        self.answer_buttons = {}  # Düymələri saxlamaq üçün
        for option in ['A', 'B', 'C', 'D', 'E']:
            btn = tk.Button(self.answer_frame, text=option, width=10, height=2,
                          command=lambda x=option: self.check_answer(x),
                          font=('Arial', 11, 'bold'))
            btn.pack(side=tk.LEFT, padx=5)
            self.answer_buttons[option] = btn
            
        # Statistika
        self.stats_label = ttk.Label(self.main_frame, text="", font=('Arial', 11))
        self.stats_label.pack(pady=10)
        
        # Düymələr çərçivəsi
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Bitir düyməsi
        self.finish_button = ttk.Button(self.button_frame, 
                                      text="Testi Bitir", 
                                      command=self.finish_quiz,
                                      style='Accent.TButton')
        self.finish_button.pack(side=tk.RIGHT, padx=5)
        
        # Stil
        self.style = ttk.Style()
        self.style.configure('Accent.TButton', 
                           font=('Arial', 11, 'bold'),
                           padding=10)
        
        # İlk sualı göstər
        self.next_question()
        
    def select_answer(self, option):
        self.answer_var.set(option)
        
    def next_question(self):
        if len(self.used_questions) == len(self.questions):
            if messagebox.askyesno("Bitiş", "Bütün suallar bitdi! Yenidən başlamaq istəyirsiniz?"):
                self.used_questions.clear()
            else:
                self.root.quit()
                return
                
        available_questions = list(set(self.questions.keys()) - self.used_questions)
        if available_questions:
            self.current_question = random.choice(available_questions)
            self.used_questions.add(self.current_question)
            
            # Sualı formatla və göstər
            question_text = self.questions[self.current_question]
            formatted_question = format_question(question_text)
            
            self.question_text.delete('1.0', tk.END)
            self.question_text.insert('1.0', f"Sual {self.current_question}:\n\n{formatted_question}")
            
            self.answer_var.set('')
            self.update_stats()
            
    def check_answer(self, selected_option):
        """Seçilmiş cavabı yoxla"""
        correct_answer = self.answers.get(self.current_question)
        
        self.total_attempted += 1
        if selected_option == correct_answer:
            self.correct_count += 1
            self.answer_buttons[selected_option].configure(bg='green', fg='white')
        else:
            self.wrong_questions.append(self.current_question)
            self.answer_buttons[selected_option].configure(bg='red', fg='white')
            self.answer_buttons[correct_answer].configure(bg='green', fg='white')
        
        self.update_stats()
        
        # 1 saniyə gözlə və növbəti suala keç
        self.root.after(1000, self.reset_and_next)
        
    def reset_and_next(self):
        """Düymələri sıfırla və növbəti suala keç"""
        # Düymələrin rəngini sıfırla
        for btn in self.answer_buttons.values():
            btn.configure(bg='SystemButtonFace', fg='black')
        
        # Növbəti suala keç
        self.next_question()
        
    def update_stats(self):
        if self.total_attempted > 0:
            percentage = (self.correct_count / self.total_attempted) * 100
            stats = (f"Ümumi: {self.total_attempted} | "
                    f"Düzgün: {self.correct_count} | "
                    f"Faiz: {percentage:.1f}% | "
                    f"Səhv: {len(self.wrong_questions)}")
        else:
            stats = "Hələ heç bir sual cavablandırılmayıb"
            
        self.stats_label.config(text=stats)
        
    def finish_quiz(self):
        """Testi bitir və nəticələri göstər"""
        if self.total_attempted == 0:
            messagebox.showinfo("Məlumat", "Hələ heç bir sual cavablandırılmayıb!")
            return
            
        result_message = "Test Nəticələri:\n\n"
        result_message += f"Ümumi cavablanan: {self.total_attempted}\n"
        result_message += f"Düzgün cavablar: {self.correct_count}\n"
        result_message += f"Səhv cavablar: {len(self.wrong_questions)}\n"
        percentage = (self.correct_count / self.total_attempted) * 100
        result_message += f"Düzgün cavab faizi: {percentage:.1f}%\n\n"
        
        if self.wrong_questions:
            result_message += "Səhv cavablandırılan suallar:\n\n"
            for q_num in self.wrong_questions:
                result_message += f"Sual {q_num}:\n"
                result_message += f"{self.questions[q_num]}\n"
                result_message += f"Düzgün cavab: {self.answers[q_num]}\n\n"
        
        # Nəticələri göstər
        result_window = tk.Toplevel(self.root)
        result_window.title("Test Nəticələri")
        result_window.geometry("600x400")
        result_window.transient(self.root)  # Əsas pəncərəyə bağlı
        result_window.grab_set()  # Modal pəncərə
        
        # Scroll edilə bilən mətn sahəsi
        text_widget = tk.Text(result_window, wrap=tk.WORD, 
                            font=('Arial', 11),
                            padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(result_window, orient=tk.VERTICAL, 
                                command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Nəticələri əlavə et
        text_widget.insert('1.0', result_message)
        text_widget.configure(state='disabled')  # Redaktəni qadağan et
        
        # Düymələr çərçivəsi
        button_frame = ttk.Frame(result_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def close_and_new():
            result_window.destroy()
            self.reset_quiz()
        
        def close_and_quit():
            result_window.destroy()
            self.root.quit()
        
        # Düymələr
        new_quiz_button = ttk.Button(button_frame, 
                                    text="Yeni Test Başlat", 
                                    command=close_and_new)
        new_quiz_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        close_button = ttk.Button(button_frame, 
                                 text="Çıxış", 
                                 command=close_and_quit)
        close_button.pack(side=tk.RIGHT, padx=5, pady=10)
        
        # Pəncərəni mərkəzləşdir
        result_window.update_idletasks()
        width = result_window.winfo_width()
        height = result_window.winfo_height()
        x = (result_window.winfo_screenwidth() // 2) - (width // 2)
        y = (result_window.winfo_screenheight() // 2) - (height // 2)
        result_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Pəncərənin bağlanmasını gözlə
        result_window.wait_window()
    
    def reset_quiz(self):
        """Testi sıfırla"""
        self.used_questions.clear()
        self.current_question = None
        self.correct_count = 0
        self.total_attempted = 0
        self.wrong_questions = []
        self.update_stats()
        self.next_question()

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()