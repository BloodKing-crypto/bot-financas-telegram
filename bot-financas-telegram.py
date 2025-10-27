import os
import json
import datetime
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Token do seu bot (SUBSTITUA pelo seu token do BotFather)
TOKEN = "SEU_TOKEN_AQUI"

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    await update.message.reply_text(
        "💰 *Bem-vindo ao seu Controle Financeiro!*\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True),
        parse_mode="Markdown"
    )

# Adicionar receita
async def adicionar_receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💵 *Adicionar Receita*\n\n"
        "Digite o valor e a descrição:\n"
        "Exemplo: 1500.00 Salário",
        parse_mode="Markdown"
    )
    context.user_data["aguardando"] = "receita"

# Adicionar despesa
async def adicionar_despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    dados = carregar_dados()
    categorias = dados["usuarios"][user_id]["categorias"]
    
    teclado_categorias = [categorias[i:i+2] for i in range(0, len(categorias), 2)]
    
    await update.message.reply_text(
        "💸 *Adicionar Despesa*\n\n"
        "Escolha a categoria:",
        reply_markup=ReplyKeyboardMarkup(teclado_categorias, resize_keyboard=True),
        parse_mode="Markdown"
    )
    context.user_data["aguardando"] = "categoria_despesa"

# Processar mensagens
async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    texto = update.message.text
    dados = carregar_dados()
    
    if "aguardando" not in context.user_data:
        await update.message.reply_text("Escolha uma opção do menu!")
        return
    
    # Processar categoria de despesa
    if context.user_data["aguardando"] == "categoria_despesa":
        categorias = dados["usuarios"][user_id]["categorias"]
        if texto in categorias:
            context.user_data["categoria"] = texto
            await update.message.reply_text(
                f"📝 *Despesa - {texto}*\n\n"
                "Digite o valor e a descrição:\n"
                "Exemplo: 45.50 Almoço restaurante",
                parse_mode="Markdown"
            )
            context.user_data["aguardando"] = "despesa"
        else:
            await update.message.reply_text("Categoria inválida!")
    
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
            
            await update.message.reply_text(
                f"✅ *Despesa registrada!*\n\n"
                f"💸 Valor: R$ {valor:.2f}\n"
                f"📝 Descrição: {descricao}\n"
                f"📂 Categoria: {categoria}\n"
                f"💰 Saldo atual: R$ {dados['usuarios'][user_id]['saldo']:.2f}",
                parse_mode="Markdown"
            )
            
            context.user_data.clear()
            
        except:
            await update.message.reply_text("Formato inválido! Use: valor descrição")
    
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
            
            await update.message.reply_text(
                f"✅ *Receita registrada!*\n\n"
                f"💵 Valor: R$ {valor:.2f}\n"
                f"📝 Descrição: {descricao}\n"
                f"💰 Saldo atual: R$ {dados['usuarios'][user_id]['saldo']:.2f}",
                parse_mode="Markdown"
            )
            
            context.user_data.clear()
            
        except:
            await update.message.reply_text("Formato inválido! Use: valor descrição")

# Ver saldo
async def ver_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    dados = carregar_dados()
    saldo = dados["usuarios"][user_id]["saldo"]
    
    cor = "🟢" if saldo >= 0 else "🔴"
    
    await update.message.reply_text(
        f"💰 *Seu Saldo*\n\n"
        f"{cor} R$ {saldo:.2f}",
        parse_mode="Markdown"
    )

# Ver extrato
async def ver_extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    dados = carregar_dados()
    transacoes = dados["usuarios"][user_id]["transacoes"][-10:]  # Últimas 10 transações
    
    if not transacoes:
        await update.message.reply_text("📭 Nenhuma transação registrada!")
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
    
    await update.message.reply_text(extrato, parse_mode="Markdown")

# Resumo por categoria
async def resumo_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("📊 Nenhuma despesa registrada para análise!")
        return
    
    resumo = "📈 *Resumo por Categoria*\n\n"
    total = sum(despesas_por_categoria.values())
    
    for categoria, valor in despesas_por_categoria.values():
        percentual = (valor / total) * 100
        resumo += f"📂 {categoria}: R$ {valor:.2f} ({percentual:.1f}%)\n"
    
    resumo += f"\n💸 Total em despesas: R$ {total:.2f}"
    
    await update.message.reply_text(resumo, parse_mode="Markdown")

# Configurar o bot
def main():
    application = Application.builder().token(TOKEN).build()
    
    # Handlers de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text("➕ Adicionar Receita"), adicionar_receita))
    application.add_handler(MessageHandler(filters.Text("➖ Adicionar Despesa"), adicionar_despesa))
    application.add_handler(MessageHandler(filters.Text("📊 Ver Saldo"), ver_saldo))
    application.add_handler(MessageHandler(filters.Text("📋 Extrato"), ver_extrato))
    application.add_handler(MessageHandler(filters.Text("📈 Resumo por Categoria"), resumo_categoria))
    
    # Handler para mensagens normais
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
    
    print("🤖 Bot iniciado! Pressione Ctrl+C para parar.")
    # Iniciar o bot
    application.run_polling()

if __name__ == "__main__":
    main()