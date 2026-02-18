"""
Image embedding model using MobileNetV2 (pretrained on ImageNet).
Extracts 1280-dimensional feature vectors from images.
"""

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms


class ImageEmbedder:
    """Wraps MobileNetV2 to generate image embeddings."""

    def __init__(self):
        # Load pretrained MobileNetV2 and remove classifier head
        weights = models.MobileNet_V2_Weights.IMAGENET1K_V1
        base_model = models.mobilenet_v2(weights=weights)

        # Use everything except the final classifier => 1280-dim feature vector
        # MobileNetV2's avg pooling is in forward(), not as a module, so add it explicitly
        self.model = nn.Sequential(
            *list(base_model.children())[:-1],
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
        )
        self.model.eval()

        # Standard ImageNet preprocessing
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    @torch.no_grad()
    def get_embedding(self, image_path: str) -> np.ndarray:
        """
        Compute a 1280-dim embedding for the image at the given path.
        Returns a 1D numpy array of shape (1280,).
        """
        img = Image.open(image_path).convert("RGB")
        tensor = self.transform(img).unsqueeze(0)  # (1, 3, 224, 224)
        features = self.model(tensor)               # (1, 1280)
        embedding = features.cpu().numpy().flatten()  # (1280,)
        # L2-normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding


# Singleton — loaded once when the module is imported
embedder = ImageEmbedder()
