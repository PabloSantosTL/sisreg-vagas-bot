import os
import sys
import json
import tkinter as tk
from tkinter import messagebox

CONFIG_FILE = "config.json"

USUARIO_FIXO = "admin"
SENHA_PADRAO = "123456"


def ler_config():
    """Lê a senha atual salva ou usa a senha padrão definida no código."""
    if not os.path.exists(CONFIG_FILE):
        salvar_config(SENHA_PADRAO)
        return {"usuario": USUARIO_FIXO, "senha": SENHA_PADRAO}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            senha_salva = dados.get("senha", "").strip()
            if not senha_salva:
                senha_salva = SENHA_PADRAO
            return {
                "usuario": USUARIO_FIXO,
                "senha": senha_salva
            }
    except Exception:
        return {"usuario": USUARIO_FIXO, "senha": SENHA_PADRAO}


def salvar_config(nova_senha):
    """Salva o usuário fixo e a senha atualizada."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"usuario": USUARIO_FIXO, "senha": nova_senha.strip()},
            f,
            indent=4,
            ensure_ascii=False
        )


def tela_login():
    credenciais = {"usuario": None, "senha": None, "autenticado": False}

    root = tk.Tk()
    root.title("Login - Automação SISREG")
    root.geometry("380x280")
    root.resizable(False, False)
    root.configure(bg="#f4f6f9")

    root.update_idletasks()
    largura = 380
    altura = 280
    x = (root.winfo_screenwidth() // 2) - (largura // 2)
    y = (root.winfo_screenheight() // 2) - (altura // 2)
    root.geometry(f"{largura}x{altura}+{x}+{y}")

    frame = tk.Frame(root, bg="#f4f6f9", padx=25, pady=20)
    frame.pack(expand=True, fill="both")

    lbl_titulo = tk.Label(
        frame,
        text="Acesso à Automação",
        font=("Segoe UI", 14, "bold"),
        bg="#f4f6f9",
        fg="#1e293b"
    )
    lbl_titulo.pack(pady=(0, 15))

    
    lbl_user = tk.Label(
        frame,
        text="Usuário:",
        font=("Segoe UI", 10, "bold"),
        bg="#f4f6f9",
        fg="#334155",
        anchor="w"
    )
    lbl_user.pack(fill="x")

    ent_user = tk.Entry(frame, font=("Segoe UI", 10), relief="solid", bd=1)
    ent_user.pack(fill="x", pady=(2, 10), ipady=4)


    lbl_pass = tk.Label(
        frame,
        text="Senha:",
        font=("Segoe UI", 10, "bold"),
        bg="#f4f6f9",
        fg="#334155",
        anchor="w"
    )
    lbl_pass.pack(fill="x")

    frame_senha = tk.Frame(frame, bg="#f4f6f9")
    frame_senha.pack(fill="x", pady=(2, 8))

    ent_pass = tk.Entry(frame_senha, font=("Segoe UI", 10), show="•", relief="solid", bd=1)
    ent_pass.pack(side="left", expand=True, fill="x", ipady=4)

    mostrar_var = tk.BooleanVar(value=False)

    def alternar_senha():
        ent_pass.config(show="" if mostrar_var.get() else "•")

    chk_mostrar = tk.Checkbutton(
        frame,
        text="Mostrar senha",
        variable=mostrar_var,
        command=alternar_senha,
        bg="#f4f6f9",
        fg="#475569",
        activebackground="#f4f6f9",
        font=("Segoe UI", 9)
    )
    chk_mostrar.pack(anchor="w", pady=(0, 12))

    def validar_login(event=None):
        config_atual = ler_config()
        u_digitado = ent_user.get().strip()
        s_digitada = ent_pass.get().strip()

        if not u_digitado or not s_digitada:
            messagebox.showwarning("Atenção", "Preencha o usuário e a senha.")
            return

        if u_digitado == config_atual["usuario"] and s_digitada == config_atual["senha"]:
            credenciais["usuario"] = config_atual["usuario"]
            credenciais["senha"] = config_atual["senha"]
            credenciais["autenticado"] = True
            root.destroy()
        else:
            messagebox.showerror("Acesso Negado", "Usuário ou senha incorretos!")
            ent_pass.delete(0, tk.END)
            ent_pass.focus_set()

    def abrir_janela_alterar_senha():
        janela_alt = tk.Toplevel(root)
        janela_alt.title("Alterar Senha")
        janela_alt.geometry("350x290")
        janela_alt.resizable(False, False)
        janela_alt.configure(bg="#f4f6f9")
        janela_alt.transient(root)
        janela_alt.grab_set()

        janela_alt.update_idletasks()
        x_alt = root.winfo_x() + (380 // 2) - (350 // 2)
        y_alt = root.winfo_y() + (280 // 2) - (290 // 2)
        janela_alt.geometry(f"350x290+{x_alt}+{y_alt}")

        f_alt = tk.Frame(janela_alt, bg="#f4f6f9", padx=25, pady=15)
        f_alt.pack(expand=True, fill="both")

        tk.Label(
            f_alt,
            text=f"Alterar senha de '{USUARIO_FIXO}'",
            font=("Segoe UI", 12, "bold"),
            bg="#f4f6f9",
            fg="#1e293b"
        ).pack(pady=(0, 12))

        tk.Label(
            f_alt,
            text="Senha Atual:",
            font=("Segoe UI", 9, "bold"),
            bg="#f4f6f9",
            fg="#334155",
            anchor="w"
        ).pack(fill="x")
        ent_atual = tk.Entry(f_alt, font=("Segoe UI", 10), show="•", relief="solid", bd=1)
        ent_atual.pack(fill="x", pady=(2, 8), ipady=3)

        tk.Label(
            f_alt,
            text="Nova Senha:",
            font=("Segoe UI", 9, "bold"),
            bg="#f4f6f9",
            fg="#334155",
            anchor="w"
        ).pack(fill="x")
        ent_nova = tk.Entry(f_alt, font=("Segoe UI", 10), show="•", relief="solid", bd=1)
        ent_nova.pack(fill="x", pady=(2, 8), ipady=3)

        tk.Label(
            f_alt,
            text="Confirmar Nova Senha:",
            font=("Segoe UI", 9, "bold"),
            bg="#f4f6f9",
            fg="#334155",
            anchor="w"
        ).pack(fill="x")
        ent_conf = tk.Entry(f_alt, font=("Segoe UI", 10), show="•", relief="solid", bd=1)
        ent_conf.pack(fill="x", pady=(2, 14), ipady=3)

        def salvar_nova_senha(event=None):
            config_atual = ler_config()
            s_atual = ent_atual.get().strip()
            s_nova = ent_nova.get().strip()
            s_conf = ent_conf.get().strip()

            if not s_atual or not s_nova or not s_conf:
                messagebox.showwarning("Atenção", "Preencha todos os campos.", parent=janela_alt)
                return

            if s_atual != config_atual["senha"]:
                messagebox.showerror("Erro", "A senha atual está incorreta!", parent=janela_alt)
                ent_atual.delete(0, tk.END)
                ent_atual.focus_set()
                return

            if s_nova != s_conf:
                messagebox.showerror("Erro", "A nova senha e a confirmação não coincidem!", parent=janela_alt)
                ent_conf.delete(0, tk.END)
                ent_conf.focus_set()
                return

            salvar_config(s_nova)
            messagebox.showinfo("Sucesso", "Senha alterada com sucesso!", parent=janela_alt)
            janela_alt.destroy()

        btn_salvar_alt = tk.Button(
            f_alt,
            text="Confirmar Alteração",
            command=salvar_nova_senha,
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            pady=6
        )
        btn_salvar_alt.pack(fill="x")

        janela_alt.bind("<Return>", salvar_nova_senha)
        ent_atual.focus_set()

    frame_botoes = tk.Frame(frame, bg="#f4f6f9")
    frame_botoes.pack(fill="x")

    btn_entrar = tk.Button(
        frame_botoes,
        text="Entrar",
        command=validar_login,
        bg="#2563eb",
        fg="white",
        activebackground="#1d4ed8",
        activeforeground="white",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=6
    )
    btn_entrar.pack(side="right", expand=True, fill="x", padx=(5, 0))

    btn_alterar = tk.Button(
        frame_botoes,
        text="Alterar Senha",
        command=abrir_janela_alterar_senha,
        bg="#e2e8f0",
        fg="#1e293b",
        activebackground="#cbd5e1",
        font=("Segoe UI", 10),
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=6
    )
    btn_alterar.pack(side="left", expand=True, fill="x", padx=(0, 5))

    root.bind("<Return>", validar_login)
    ent_user.focus_set()

    root.mainloop()

    if not credenciais["autenticado"]:
        print("\nLogin cancelado pelo usuário.")
        sys.exit(0)

    return credenciais["usuario"], credenciais["senha"]


if __name__ == "__main__":
    u, s = tela_login()
    print(f"Login validado com sucesso para o usuário: {u}")