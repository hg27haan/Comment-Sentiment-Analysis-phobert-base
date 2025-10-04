import torch
from transformers import pipeline

model_id = 'hghaan/Sentiment-Analysis-phobert-base'

device = 0 if torch.cuda.is_available() else -1
classifier = pipeline('sentiment-analysis', model=model_id, device=device)

reviews = [
    "Sản phẩm này chất lượng quá tuyệt vời, giao hàng cũng nhanh nữa!",
    "Pin dùng nhanh hết, mới sạc đầy mà dùng 2 tiếng đã hết pin rồi.",
    "Cũng tạm được, không có gì đặc sắc lắm so với giá tiền.",
    "Shop lừa đảo, giao hàng không đúng mẫu, nhắn tin không trả lời."
]

results = classifier(reviews)

label_map = {
    'LABEL_0': 'Negative',
    'LABEL_1': 'Neutral',
    'LABEL_2': 'Positive'
    }

for review, result in zip(reviews, results):
    label_name = label_map.get(result['label'], result['label'])
    score = result['score'] * 100
    print(f"Review: {review}\nSentiment: {label_name}, Score: {result['score']:.4f}\n")
    

