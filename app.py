import json
import tkinter as tk
from tkinter import ttk, messagebox
from engine import AspaDatabase, CheckInput, check

BASE = __import__('pathlib').Path(__file__).parent

def load_db():
    data = json.loads((BASE / 'dataset.json').read_text())
    return AspaDatabase(data['records'], set(data.get('missing', [])))

def parse_path(text):
    text = text.replace(',', ' ').strip()
    return [] if not text else [int(x) for x in text.split()]

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AIORI-3 PS-031 | Offline ASPA BGP Export Policy Checker')
        self.geometry('980x720')
        self.db = load_db()
        self._build()
        self.load_example()

    def _build(self):
        pad = {'padx': 8, 'pady': 5}
        ttk.Label(self, text='Offline ASPA-Based BGP Export Policy Checker', font=('TkDefaultFont', 16, 'bold')).pack(anchor='w', **pad)
        ttk.Label(self, text='Prototype: paths are entered in BGP display order (most recently added AS first, origin AS last).').pack(anchor='w', **pad)
        form = ttk.LabelFrame(self, text='Export policy context and AS_PATH')
        form.pack(fill='x', **pad)
        self.local = tk.StringVar(value='64500'); self.neighbor = tk.StringVar(value='65001'); self.path = tk.StringVar(value='65001 65002 65003')
        self.rel = tk.StringVar(value='provider'); self.as_set = tk.BooleanVar(); self.aug = tk.BooleanVar(); self.rs = tk.BooleanVar()
        for col, label, var in [(0,'Local AS',self.local),(1,'Neighbor AS',self.neighbor),(2,'AS_PATH',self.path)]:
            ttk.Label(form, text=label).grid(row=0,column=col,sticky='w',**pad)
            ttk.Entry(form, textvariable=var, width=30 if col==2 else 14).grid(row=1,column=col,sticky='ew',**pad)
        ttk.Label(form, text='Neighbor relationship').grid(row=2,column=0,sticky='w',**pad)
        ttk.Combobox(form, textvariable=self.rel, values=['provider','peer','customer'], state='readonly', width=12).grid(row=3,column=0,sticky='w',**pad)
        ttk.Checkbutton(form, text='AS_SET present', variable=self.as_set).grid(row=3,column=1,sticky='w',**pad)
        ttk.Checkbutton(form, text='Neighbor-AS augmented mode', variable=self.aug).grid(row=3,column=2,sticky='w',**pad)
        ttk.Checkbutton(form, text='Route-server-client exception', variable=self.rs).grid(row=4,column=0,sticky='w',**pad)
        ttk.Button(form, text='Check export', command=self.run_check).grid(row=4,column=2,sticky='e',**pad)
        for i in range(3): form.columnconfigure(i, weight=1)

        self.status = tk.StringVar(value='—')
        out = ttk.LabelFrame(self, text='Verification result')
        out.pack(fill='both', expand=True, **pad)
        ttk.Label(out, textvariable=self.status, font=('TkDefaultFont', 22, 'bold')).pack(anchor='w', **pad)
        self.summary = tk.Text(out, height=7, wrap='word'); self.summary.pack(fill='x', **pad); self.summary.configure(state='disabled')
        ttk.Label(out, text='Audit trail').pack(anchor='w', **pad)
        self.audit = tk.Text(out, wrap='word'); self.audit.pack(fill='both', expand=True, **pad); self.audit.configure(state='disabled')
        ttk.Button(self, text='Load valid example', command=self.load_example).pack(anchor='w', **pad)

    def load_example(self):
        self.local.set('64500'); self.neighbor.set('65001'); self.rel.set('provider'); self.path.set('65001 65002 65003')
        self.as_set.set(False); self.aug.set(False); self.rs.set(False)
        self.run_check()

    def _set_text(self, widget, text):
        widget.configure(state='normal'); widget.delete('1.0','end'); widget.insert('1.0', text); widget.configure(state='disabled')

    def run_check(self):
        try:
            inp = CheckInput(int(self.local.get()), int(self.neighbor.get()), self.rel.get(), parse_path(self.path.get()), self.as_set.get(), self.aug.get(), self.rs.get())
            result = check(inp, self.db)
        except Exception as exc:
            messagebox.showerror('Input error', str(exc)); return
        self.status.set(result.status)
        self.summary.configure(foreground={'Valid':'#147a2e','Invalid':'#b00020','Unknown':'#9a6700'}.get(result.status, 'black'))
        summary = '\n'.join(result.reasons) + f"\n\nProcedure: {result.procedure}\nCompressed path: {' '.join(map(str,result.compressed_path)) or '(empty)'}\nRamp bounds: max_up={result.max_up_ramp}, min_up={result.min_up_ramp}, max_down={result.max_down_ramp}, min_down={result.min_down_ramp}"
        self._set_text(self.summary, summary)
        lines = []
        for i, item in enumerate(result.audit, 1):
            lines.append(f"{i}. {item['direction'].upper()} {item['customer']} -> {item['provider']}: {item['authorization']} — {item['note']}")
        self._set_text(self.audit, '\n'.join(lines) if lines else 'No ramp authorization lookups were needed.')

if __name__ == '__main__':
    App().mainloop()
