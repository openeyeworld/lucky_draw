import csv
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import collections
import os
import time
import sys

# 导入 pygame
import pygame
import pygame.freetype

# 资源路径兼容处理（用于 Pyinstaller 封装）
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class UltimateLuckyDrawV23:
    def __init__(self, root):
        self.root = root
        self.root.title("2026年会抽奖系统 - V23 终极防闪烁版")
        self.root.geometry("1300x850")
        
        self.all_attendees = []             
        self.winners_dict = collections.OrderedDict() 
        self.target_font_family = "Microsoft YaHei"
        
        # 配色方案
        self.color_schemes = {
            "庆典红 (经典)": {"text": (230, 74, 25), "bg": (255, 255, 255)},
            "流沙金 (高亮)": {"text": (255, 215, 0), "bg": (20, 20, 20)},
            "极光蓝 (科技)": {"text": (0, 242, 255), "bg": (10, 15, 30)},
            "象牙白 (反转)": {"text": (255, 255, 255), "bg": (0, 0, 0)},
            "霓虹绿 (极光)": {"text": (57, 255, 20), "bg": (15, 15, 15)}
        }
        
        # 奖项 UI 背景色 (管理后台使用)
        self.prize_ui_styles = {
            "特等奖": {"fg": "#FFFFFF", "bg": "#D32F2F"}, 
            "一等奖": {"fg": "#FFFFFF", "bg": "#F57C00"}, 
            "二等奖": {"fg": "#000000", "bg": "#FFEB3B"}, 
            "三等奖": {"fg": "#FFFFFF", "bg": "#1976D2"}  
        }

        self.setup_ui()

    def setup_ui(self):
        left_frame = tk.Frame(self.root, width=350, bg="#f5f5f5")
        left_frame.pack(side="left", fill="y")
        
        inner_left = tk.Frame(left_frame, bg="#f5f5f5")
        inner_left.pack(padx=20, pady=20)

        tk.Label(inner_left, text="管理控制中心", font=(self.target_font_family, 18, "bold"), bg="#f5f5f5").pack(pady=15)

        # 1. 名单导入
        file_frame = tk.LabelFrame(inner_left, text="1. 名单导入与去重", padx=10, pady=10)
        file_frame.pack(fill="x", pady=5)
        tk.Button(file_frame, text="📁 导入 CSV 名单", command=self.load_file, bg="#ffffff").pack(fill="x")
        self.info_label = tk.Label(file_frame, text="等待导入...", fg="gray")
        self.info_label.pack(pady=5)

        # 2. 抽奖配置
        config_frame = tk.LabelFrame(inner_left, text="2. 视觉与参数配置", padx=10, pady=10)
        config_frame.pack(fill="x", pady=5)
        
        tk.Label(config_frame, text="抽取奖项:").grid(row=0, column=0, sticky="w", pady=5)
        self.prize_name_var = tk.StringVar(value="三等奖")
        ttk.Combobox(config_frame, textvariable=self.prize_name_var, values=list(self.prize_ui_styles.keys()), width=12).grid(row=0, column=1, pady=5)
        
        tk.Label(config_frame, text="抽取人数:").grid(row=1, column=0, sticky="w", pady=5)
        self.count_spinner = tk.Spinbox(config_frame, from_=1, to=1000, width=11)
        self.count_spinner.grid(row=1, column=1, pady=5)

        tk.Label(config_frame, text="屏幕配色:").grid(row=2, column=0, sticky="w", pady=5)
        self.scheme_var = tk.StringVar(value="庆典红 (经典)")
        ttk.Combobox(config_frame, textvariable=self.scheme_var, values=list(self.color_schemes.keys()), width=12).grid(row=2, column=1, pady=5)

        self.allow_repeat = tk.BooleanVar(value=False)
        tk.Checkbutton(config_frame, text="允许跨奖项重复中奖", variable=self.allow_repeat).grid(row=3, column=0, columnspan=2, sticky="w")

        # 3. 动作
        self.start_btn = tk.Button(inner_left, text="⚡ 进入全屏抽奖", command=self.launch_pygame, 
                                   state="disabled", bg="#2E7D32", fg="white", 
                                   font=(self.target_font_family, 13, "bold"), pady=15)
        self.start_btn.pack(fill="x", pady=20)
        
        tk.Button(inner_left, text="💾 导出中奖名单", command=self.export_winners, bg="#1976D2", fg="white").pack(fill="x")

        # --- 右侧中奖汇总 (高可读性设计) ---
        right_frame = tk.Frame(self.root, bg="white")
        right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(right_frame, text="中奖记录汇总 (分色显示)", font=(self.target_font_family, 14, "bold"), bg="white").pack(anchor="w", pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=40, font=(self.target_font_family, 11))
        style.configure("Treeview.Heading", font=(self.target_font_family, 11, "bold"))

        self.result_tree = ttk.Treeview(right_frame, columns=("id", "prize", "winner"), show="headings")
        self.result_tree.heading("id", text="序号")
        self.result_tree.heading("prize", text="奖项等级")
        self.result_tree.heading("winner", text="姓名")
        self.result_tree.column("id", width=80, anchor="center")
        self.result_tree.pack(side="left", fill="both", expand=True)

        for p_name, style_cfg in self.prize_ui_styles.items():
            self.result_tree.tag_configure(p_name, background=style_cfg["bg"], foreground=style_cfg["fg"])

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path: return
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                raw = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]
            
            counts = collections.Counter(raw)
            duplicates = {name: count for name, count in counts.items() if count > 1}
            
            if duplicates:
                dup_msg = "\n".join([f"· {k}: {v}次" for k, v in list(duplicates.items())[:5]])
                msg = f"检测到 {len(duplicates)} 组重复姓名！\n\n部分列表：\n{dup_msg}\n\n是否一键去重？"
                choice = messagebox.askyesnocancel("重复检测提醒", msg)
                if choice is True: self.all_attendees = list(collections.OrderedDict.fromkeys(raw))
                elif choice is False: self.all_attendees = raw
                else: return
            else:
                self.all_attendees = raw
                
            self.info_label.config(text=f"已加载: {len(self.all_attendees)} 人", fg="#2E7D32")
            self.start_btn.config(state="normal")
        except Exception as e: messagebox.showerror("错误", str(e))

    def update_tree(self):
        for item in self.result_tree.get_children(): self.result_tree.delete(item)
        idx = 1
        for p_name, names in self.winners_dict.items():
            for name in names:
                self.result_tree.insert("", "end", values=(f"{idx:03d}", p_name, name), tags=(p_name,))
                idx += 1

    def launch_pygame(self):
        try: target_num = int(self.count_spinner.get())
        except: return
        prize_name = self.prize_name_var.get()
        all_won = [n for names in self.winners_dict.values() for n in names]
        current_pool = [n for n in self.all_attendees if n not in all_won] if not self.allow_repeat.get() else list(self.all_attendees)
        
        if len(current_pool) < target_num:
            messagebox.showwarning("警告", "当前可用人数不足。")
            return
            
        selected_scheme = self.color_schemes[self.scheme_var.get()]
        
        # 彻底隐藏 Tk 窗口，减少闪烁
        self.root.withdraw()
        self.root.update()
        time.sleep(0.2) # 给显卡切换时间
        self.pygame_loop(prize_name, target_num, current_pool, selected_scheme)

    def pygame_loop(self, p_name, target_num, pool, scheme):
        # 强制设置 SDL 驱动居中
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.freetype.init()
        
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except: pass

        # --- 终极防闪烁窗口创建 ---
        # 1. 开启双缓冲 DOUBLEBUF 
        # 2. 开启硬件加速 HWSURFACE 
        # 3. 强制垂直同步 vsync=1 (关键！)
        try:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE, vsync=1)
        except:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        
        sw, sh = screen.get_size()
        txt_color, bg_color = scheme["text"], scheme["bg"]

        # 字体路径加载
        internal_font = resource_path("msyh.ttc")
        system_font = "C:\\Windows\\Fonts\\msyhbd.ttc"
        font_path = internal_font if os.path.exists(internal_font) else (system_font if os.path.exists(system_font) else None)

        try:
            if font_path:
                font_big = pygame.freetype.Font(font_path, 150)
                font_mid = pygame.freetype.Font(font_path, 42)
                font_small = pygame.freetype.Font(font_path, 24)
            else:
                font_big = pygame.freetype.SysFont("microsoftyahei", 150)
                font_mid = pygame.freetype.SysFont("microsoftyahei", 42)
                font_small = pygame.freetype.SysFont("microsoftyahei", 24)
        except:
            font_big = pygame.freetype.SysFont(None, 150)
            font_mid = pygame.freetype.SysFont(None, 42)
            font_small = pygame.freetype.SysFont(None, 24)

        clock = pygame.time.Clock()
        running, state, current_winners = True, "WAITING", []
        display_name = "READY"
        pygame.event.clear()

        # 预热填充背景，防止第一帧白屏/闪烁
        screen.fill(bg_color)
        pygame.display.flip()

        while running:
            # 每一帧的开始都先重绘背景 (逻辑上的双缓冲)
            screen.fill(bg_color)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: running = False
                    if event.key == pygame.K_SPACE:
                        if state in ["WAITING", "SHOW_WINNER"]:
                            if len(current_winners) < target_num: state = "ROLLING"
                            else: state = "SUMMARY"
                        elif state == "ROLLING":
                            winner = random.choice(pool)
                            display_name = winner
                            current_winners.append(winner)
                            if not self.allow_repeat.get(): pool.remove(winner)
                            if p_name not in self.winners_dict: self.winners_dict[p_name] = []
                            self.winners_dict[p_name].append(winner)
                            state = "SHOW_WINNER"
                        elif state == "SUMMARY": running = False

            # --- 绘制逻辑 ---
            if state != "SUMMARY":
                font_mid.render_to(screen, (sw//2 - font_mid.get_rect(f"正在抽取：{p_name}").width//2, 100), f"正在抽取：{p_name}", (150, 150, 150))
                
                if state == "ROLLING": display_name = random.choice(self.all_attendees)
                
                t_size = 150
                rect = font_big.get_rect(display_name, size=t_size)
                while rect.width > sw * 0.85 and t_size > 10:
                    t_size -= 5
                    rect = font_big.get_rect(display_name, size=t_size)
                
                font_big.render_to(screen, (sw//2 - rect.width//2, sh//2 - rect.height//2), display_name, txt_color, size=max(1, t_size))
                
                rem = target_num - len(current_winners)
                hint = f"剩余: {rem} | [空格] 开始/停止"
                if rem == 0 and state == "SHOW_WINNER": hint = "本轮完成！按 [空格] 总结"
                font_small.render_to(screen, (sw//2 - font_small.get_rect(hint).width//2, sh - 100), hint, (130, 130, 130))
            else:
                # 总结页
                font_mid.render_to(screen, (sw//2 - font_mid.get_rect(f"{p_name} 获奖名单").width//2, 80), f"{p_name} 获奖名单", txt_color)
                cols = 4 if target_num > 12 else (2 if target_num <= 6 else 3)
                col_w, row_h = sw // (cols + 1), 65
                for i, name in enumerate(current_winners):
                    r, c = divmod(i, cols)
                    s_size = 35
                    n_rect = font_mid.get_rect(name, size=s_size)
                    while n_rect.width > col_w * 0.85 and s_size > 5:
                        s_size -= 2
                        n_rect = font_mid.get_rect(name, size=s_size)
                    font_mid.render_to(screen, (col_w*(c+1)-n_rect.width//2, 220+r*row_h), name, txt_color, size=max(1, s_size))
            
            # 刷新屏幕
            pygame.display.flip()
            # 限制 60 FPS，防止 CPU 过热导致系统强制调节电压产生闪烁
            clock.tick(60)

        pygame.quit()
        self.root.deiconify()
        self.root.state('normal')
        self.root.focus_force()
        self.root.update()
        self.update_tree()

    def export_winners(self):
        if not self.winners_dict: return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            try:
                with open(path, mode='w', encoding='utf-8-sig', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(["序号", "奖项", "姓名"])
                    idx = 1
                    for p, names in self.winners_dict.items():
                        for n in names: w.writerow([idx, p, n]); idx += 1
                messagebox.showinfo("成功", "名单已导出。")
            except Exception as e: messagebox.showerror("导出失败", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    app = UltimateLuckyDrawV23(root)
    root.mainloop()
