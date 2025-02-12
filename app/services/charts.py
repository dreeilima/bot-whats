import matplotlib.pyplot as plt
import io
import base64

class ChartService:
    @staticmethod
    def generate_expense_pie_chart(categories: dict) -> str:
        """Gera gráfico de pizza de despesas por categoria"""
        plt.figure(figsize=(10, 8))
        plt.pie(
            categories.values(),
            labels=categories.keys(),
            autopct='%1.1f%%',
            colors=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99CCFF']
        )
        plt.title('Despesas por Categoria')
        
        # Salva o gráfico em bytes
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png')
        img_bytes.seek(0)
        
        # Converte para base64
        return base64.b64encode(img_bytes.read()).decode()

    @staticmethod
    def generate_monthly_comparison_chart(months: list, values: list) -> str:
        """Gera gráfico de barras comparando meses"""
        plt.figure(figsize=(12, 6))
        plt.bar(months, values, color='#66B2FF')
        plt.title('Comparação Mensal de Gastos')
        plt.xlabel('Mês')
        plt.ylabel('Valor (R$)')
        
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png')
        img_bytes.seek(0)
        
        return base64.b64encode(img_bytes.read()).decode()

    @staticmethod
    def generate_savings_progress_chart(target: float, current: float) -> str:
        """Gera gráfico de progresso da meta de economia"""
        plt.figure(figsize=(8, 3))
        plt.barh(['Progresso'], [current], color='#99FF99')
        plt.barh(['Progresso'], [target-current], left=[current], color='#FFCCCC')
        plt.xlim(0, target)
        plt.title(f'Progresso da Meta: {(current/target)*100:.1f}%')
        
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png')
        img_bytes.seek(0)
        
        return base64.b64encode(img_bytes.read()).decode() 