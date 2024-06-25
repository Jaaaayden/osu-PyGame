import pygame

BASE_IMG_PATH = ''

def load_image(path, transparent):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey(transparent)
    return img