import os
import json
import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Token do Render (lê da variável de ambiente)
TOKEN = os.environ.get('8476552838:AAGhs2dtuuNlBo8M-RMVaDlSKd7lKidOZOw')

# Arquivo para salvar dados
DATA_FILE = "financas.json"

# Carregar dados salvos
def carregar_dados():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"usuarios": {}}

# Salvar dados
def salvar_dados(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f)

# Comando /start
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    dados = carregar_dados()
    
    if user_id not in dados["usuarios"]:
        dados["usuarios"][user_id] = {
            "saldo": 0,
            "transacoes": [],
            "categorias": ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Outros"]
        }
        salvar_dados(dados)
    
    teclado = [
        ["➕ Adicionar Receita", "➖ Adicionar Despesa"],
        ["📊 Ver Saldo", "📋 Extrato"],
        ["📈 Resumo por Categoria"]
    ]
    
    update.message.reply_text(
        "💰 *Bem-vindo ao seu Controle Financeiro!*\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True),
        parse_mode="Markdown"
    )

# Adicionar receita
def adicionar_receita(update: Update, context: CallbackContext):
    update.message.reply_text(
        "💵 *Adicionar Receita*\n\n"
        "Digite o valor e a descrição:\n"
        "Exemplo: 1500.00 Salário",
        parse_mode="Markdown"
    )
    context.user_data["aguardando"] = "receita"

# Adicionar despesa
def adicionar_despesa(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    dados = carregar_dados()
    categorias = dados["usuarios"][user_id]["categorias"]
    
    teclado_categorias = [categorias[i:i+2] for i in range(0, len(categorias), 2)]
    
    update.message.reply_text(
        "💸 *Adicionar Despesa*\n\n"
        "Escolha a categoria:",
        reply_markup=ReplyKeyboardMarkup(teclado_categorias, resize_keyboard=True),
        parse_mode="Markdown"
    )
    context.user_data["aguardando"] = "categoria_despesa"

# Processar mensagens
def processar_mensagem(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    texto = update.message.text
    dados = carregar_dados()
    
    if "aguardando" not in context.user_data:
        update.message.reply_text("Escolha uma opção do menu!")
        return
    
    # Processar categoria de despesa
    if context.user_data["aguardando"] == "categoria_despesa":
        categorias = dados["usuarios"][user_id]["categorias"]
        if texto in categorias:
            context.user_data["categoria"] = texto
            update.message.reply_text(
                f"📝 *Despesa - {texto}*\n\n"
                "Digite o valor e a descrição:\n"
                "Exemplo: 45.50 Almoço restaurante",
                parse_mode="Markdown"
            )
            context.user_data["aguardando"] = "despesa"
        else:
            update.message.reply_text("Categoria inválida!")
    
    # Processar despesa
    elif context.user_data["aguardando"] == "despesa":
        try:
            partes = texto.split(" ", 1)
            valor = float(partes[0])
            descricao = partes[1] if len(partes) > 1 else "Sem descrição"
            categoria = context.user_data["categoria"]
            
            transacao = {
                "tipo": "despesa",
                "valor": valor,
                "descricao": descricao,
                "categoria": categoria,
                "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            dados["usuarios"][user_id]["transacoes"].append(transacao)
            dados["usuarios"][user_id]["saldo"] -= valor
            salvar_dados(dados)
            
            update.message.reply_text(
                f"✅ *Despesa registrada!*\n\n"
                f"💸 Valor: R$ {valor:.2f}\n"
                f"📝 Descrição: {descricao}\n"
                f"📂 Categoria: {categoria}\n"
                f"💰 Saldo atual: R$ {dados['usuarios'][user_id]['saldo']:.2f}",
                parse_mode="Markdown"
            )
            
            context.user_data.clear()
            
        except:
            update.message.reply_text("Formato inválido! Use: valor descrição")
    
    # Processar receita
    elif context.user_data["aguardando"] == "receita":
        try:
            partes = texto.split(" ", 1)
            valor = float(partes[0])
            descricao = partes[1] if len(partes) > 1 else "Sem descrição"
            
            transacao = {
                "tipo": "receita",
                "valor": valor,
                "descricao": descricao,
                "categoria": "Receita",
                "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            dados["usuarios"][user_id]["transacoes"].append(transacao)
            dados["usuarios"][user_id]["saldo"] += valor
            salvar_dados(dados)
            
            update.message.reply_text(
                f"✅ *Receita registrada!*\n\n"
                f"💵 Valor: R$ {valor:.2f}\n"
                f"📝 Descrição: {descricao}\n"
                f"💰 Saldo atual: R$ {dados['usuarios'][user_id]['saldo']:.2f}",
                parse_mode="Markdown"
            )
            
            context.user_data.clear()
            
        except:
            update.message.reply_text("Formato inválido! Use: valor descrição")

# Ver saldo
def ver_saldo(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    dados = carregar_dados()
    saldo = dados["usuarios"][user_id]["saldo"]
    
    cor = "🟢" if saldo >= 0 else "🔴"
    
    update.message.reply_text(
        f"💰 *Seu Saldo*\n\n"
        f"{cor} R$ {saldo:.2f}",
        parse_mode="Markdown"
    )

# Ver extrato
def ver_extrato(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    dados = carregar_dados()
    transacoes = dados["usuarios"][user_id]["transacoes"][-10:]  # Últimas 10 transações
    
    if not transacoes:
        update.message.reply_text("📭 Nenhuma transação registrada!")
        return
    
    extrato = "📋 *Últimas Transações*\n\n"
    
    for transacao in reversed(transacoes):
        icone = "💵" if transacao["tipo"] == "receita" else "💸"
        sinal = "+" if transacao["tipo"] == "receita" else "-"
        extrato += f"{icone} {transacao['data']}\n"
        extrato += f"{sinal} R$ {transacao['valor']:.2f} - {transacao['descricao']}\n"
        if transacao["tipo"] == "despesa":
            extrato += f"📂 {transacao['categoria']}\n"
        extrato += "───────\n"
    
    update.message.reply_text(extrato, parse_mode="Markdown")

# Resumo por categoria
def resumo_categoria(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    dados = carregar_dados()
    transacoes = dados["usuarios"][user_id]["transacoes"]
    
    despesas_por_categoria = {}
    
    for transacao in transacoes:
        if transacao["tipo"] == "despesa":
            categoria = transacao["categoria"]
            if categoria not in despesas_por_categoria:
                despesas_por_categoria[categoria] = 0
            despesas_por_categoria[categoria] += transacao["valor"]
    
    if not despesas_por_categoria:
        update.message.reply_text("📊 Nenhuma despesa registrada para análise!")
        return
    
    resumo = "📈 *Resumo por Categoria*\n\n"
    total = sum(despesas_por_categoria.values())
    
    for categoria, valor in despesas_por_categoria.items():
        percentual = (valor / total) * 100
        resumo += f"📂 {categoria}: R$ {valor:.2f} ({percentual:.1f}%)\n"
    
    resumo += f"\n💸 Total em despesas: R$ {total:.2f}"
    
    update.message.reply_text(resumo, parse_mode="Markdown")

# Configurar o bot
def main():
    if not TOKEN:
        print("❌ ERRO: Token não encontrado! Configure a variável TOKEN no Render.")
        return
    
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Handlers de comandos
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text("➕ Adicionar Receita"), adicionar_receita))
    dispatcher.add_handler(MessageHandler(Filters.text("➖ Adicionar Despesa"), adicionar_despesa))
    dispatcher.add_handler(MessageHandler(Filters.text("📊 Ver Saldo"), ver_saldo))
    dispatcher.add_handler(MessageHandler(Filters.text("📋 Extrato"), ver_extrato))
    dispatcher.add_handler(MessageHandler(Filters.text("📈 Resumo por Categoria"), resumo_categoria))
    
    # Handler para mensagens normais
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))
    
    print("🤖 Bot iniciado no Render!")
    # Iniciar o bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
