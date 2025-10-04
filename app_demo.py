import gradio as gr
from transformers import pipeline
import torch

print('Đang tải model....')
model_id = 'hghaan/Sentiment-Analysis-phobert-base'
device = 0 if torch.cuda.is_available() else -1
classifier = pipeline('sentiment-analysis', model=model_id, device=device)
print('Tải model xong!')

def predict_sentiment(review_text):
    if not review_text.strip():
        return "Vui lòng nhập đánh giá hợp lệ."
    
    predictions = classifier([review_text], return_all_scores=True)

    label_map = {
        'LABEL_0': 'Tiêu cực',
        'LABEL_1': 'Trung lập',
        'LABEL_2': 'Tích cực'
    }

    formatted_results = {label_map.get(item['label'], item['label']): item['score'] for item in predictions[0]}
    return formatted_results


description = """
Đây là ứng dụng dùng để dự đoán mức độ cảm xúc của đánh giá sản phẩm bằng mô hình học sâu PhoBERT.
- Nhập đánh giá sản phẩm vào ô bên dưới.
- Nhấn nút "Dự đoán" để xem kết quả phân loại cảm xúc.
"""

demo = gr.Interface(
    fn=predict_sentiment,
    inputs=gr.Textbox(lines=5, label="Bình luận sản phẩm", placeholder="Nhập đánh giá sản phẩm ở đây..."),
    outputs=gr.Label(num_top_classes=3, label="Kết quả dự đoán"),
    title="Phân tích cảm xúc đánh giá sản phẩm",
    description=description,
    theme="compact"
)

if __name__ == "__main__":
    demo.launch()