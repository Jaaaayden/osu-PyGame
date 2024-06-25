import pygame
from pygame import mixer
import random
import sys
import soundfile
import librosa
from utils import load_image
import asyncio

pygame.display.set_caption("osu! inspired")
#python -m pygbag CSP

"""
Images and songs are pulled from the following:
https://youtu.be/v2H4l9RpkwM?si=ExCXzNHXX6AgmGM6
https://youtu.be/5xfNTyy-Xhk?si=R-idcmrRsm2tchn_
https://youtu.be/u3kRzdSnsTA?si=v0-xxkI2FRU1_zyF
https://youtu.be/fmI_Ndrxy14?si=AisPn6RRWRlaeMST
https://youtu.be/6VNeYr8h72o?si=YDgiaTHilQNU8_Ia
https://cutewallpaper.org/21/osu-menu-background/view-page-21.html
https://osuskinner.com/standard
https://osu.ppy.sh/home
""" 

clock = pygame.time.Clock() 

screenWidth = 1280
screenHeight = 720
screen = pygame.display.set_mode((screenWidth, screenHeight)) # creating screen dimensions

beat_event = pygame.USEREVENT +1 # custom event 

pygame.init()
pygame.mixer.init(44100, -16, 2, 2048) # better quality audio

font = pygame.font.Font("fonts/OpenSans-Regular.ttf", 40) # loading font/song
big_font = pygame.font.Font("fonts/OpenSans-Regular.ttf", 60)

if sys.platform == "emscripten":
    song = mixer.music.load("sounds/welcome.ogg")
    mixer.music.play()
else:
    song = mixer.music.load("sounds/welcome.wav")
    mixer.music.play()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

GREEN = (60, 179, 113)
YELLOW = (240, 230, 140)
RED = (205, 92, 92)
DARK_RED = (139, 0, 0)

if sys.platform == "emscripten":
    hit_sound = pygame.mixer.Sound("sounds/hitsound.ogg")
else:
    hit_sound = pygame.mixer.Sound("sounds/hitsound.wav")

hit_sound.set_volume(0.5)

SS_rank = pygame.image.load("assets/SS.png")
S_rank = pygame.image.load("assets/S.png")
A_rank = pygame.image.load("assets/A.png")
B_rank = pygame.image.load("assets/B.png")
C_rank = pygame.image.load("assets/C.png")
D_rank = pygame.image.load("assets/D.png")
cursor_img = pygame.image.load("assets/cursor_img.png")

hit_circle = load_image("assets/hitcircle.png", (0, 0, 0))
x_pos = 605
y_pos = 340

# if song isn't changed, defaulted to Padoru
approach_radius = 200 # initial approach circle radius
game_start = False # actually having the screen update notes
song_start = False # purely to start song

multi_click = False # prevent shenanigans (double clicking same circle)
game_over = False # when last note is played, score screen
song_name = "Padoru" # changes depending on user input on first screen

# data collected
perfect_hit = 0
good_hit = 0
early_hit = 0
combo = 0
max_combo = 0

def start_song():
    global song
    if sys.platform == "emscripten":
        song = mixer.music.load("sounds/" + song_name + ".ogg")
        mixer.music.set_volume(0.6)
        mixer.music.play()
    else:
        song = mixer.music.load("sounds/" + song_name + ".wav")
        mixer.music.set_volume(0.6)
        mixer.music.play()

def song_tempo():
    # code to determine approximate beats per second https://dev.to/highcenburg/getting-the-tempo-of-a-song-using-librosa-4e5b
    if sys.platform == "emscripten":
        audio_file = librosa.load("sounds/" + song_name + ".ogg")
    else:
        audio_file = librosa.load("sounds/" + song_name + ".wav")
    y, sr = audio_file
    
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    
    beat_times = []
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
    beat_times.insert(0, 0)
    
    #print(beat_times)
    return beat_times

beat_times = song_tempo()
score = 0
current_beat = 1
last_hit = ""
current_max_score = 3*current_beat
total_beats = len(beat_times) - 1
max_score = 3*(len(beat_times) - 1)
      
def song_select_update(): # when user changes song in selection screen
    global total_beats, max_score, song_name, song_bg
    song_bg = pygame.image.load("assets/" + song_name + ".jpg")
    if song_name == "Padoru" or song_name == "Warriors":
        song_bg = imageScaling(0, 0, song_bg, 1.05)
    else:
        song_bg = imageScaling(0, 0, song_bg, 0.7)
    total_beats = len(beat_times) - 1
    max_score = 3*(len(beat_times) - 1)

def draw_screen(): # draws 60 times per second 
    global approach_radius, hit_circle, x_pos, y_pos
    song_bg.draw()
    framesNextBeat = (beat_times[current_beat]- beat_times[current_beat - 1])*60 # calculates number of frames between current and next beat
    approach_radius -= 130/framesNextBeat # radius needs to change from 200 -> 70 over the course of framesNextBeat
    
    hit_circle_object.draw() # method defined below
    scoreText = font.render("Score: " + str(score), True, RED)
    screen.blit(scoreText, (1025, 30))     
    
    if last_hit == "perfect":
        lastHitScore = font.render("+3", True, GREEN)
        screen.blit(lastHitScore, (950, 30))
    elif last_hit == "good":
        lastHitScore = font.render("+2", True, YELLOW)
        screen.blit(lastHitScore, (950, 30))
    elif last_hit == "early":
        lastHitScore = font.render("+1", True, RED)
        screen.blit(lastHitScore, (950, 30))
    elif last_hit == "miss": 
        lastHitScore = font.render("MISS", True, DARK_RED)
        screen.blit(lastHitScore, (900, 30))
        
    percentText = font.render("Accuracy: " + f"{score/current_max_score:.0%}", True, RED) 
    screen.blit(percentText, (975, 100))
    
    if last_hit == "miss": 
        combo_text = font.render("Combo: " + str(combo), True, DARK_RED)
        screen.blit(combo_text, (0, 590))
    else:
        combo_text = font.render("Combo: " + str(combo), True, RED)
        screen.blit(combo_text, (0, 590))
        
    if approach_radius >= 150: # three colors of approach circle, click when green
        pygame.draw.circle(screen, RED, (x_pos+65, y_pos+65), approach_radius, width=6)
    elif approach_radius >= 100:
        pygame.draw.circle(screen, YELLOW, (x_pos+65, y_pos+65), approach_radius, width=6)
    else:
        pygame.draw.circle(screen, GREEN, (x_pos+65, y_pos+65), approach_radius, width=6) 
    cursor_img_rect.center = pygame.mouse.get_pos()  # update position 
    screen.blit(cursor_img, cursor_img_rect) # draw the cursor
        
def score_tally(): # when song is completed
    name = big_font.render("Song: " + song_name, True, DARK_RED)
    screen.blit(name, (450, 150))
    finalScore = font.render("Score: " + str(score) + " / " + str(max_score), True, BLACK)
    screen.blit(finalScore, (500, 250))
    percentText = font.render("Accuracy: " + f"{score/max_score:.0%}", True, RED) 
    screen.blit(percentText, (500, 300))
    maxCombo = font.render("Max Combo: " + str(max_combo), True, RED)
    screen.blit(maxCombo, (500, 350))
    
    perfect = font.render("Perfect Hits: " + str(perfect_hit), True, GREEN) 
    screen.blit(perfect, (500, 450))
    
    good = font.render("Good Hits: " + str(good_hit), True, YELLOW) 
    screen.blit(good, (500, 500))
        
    early = font.render("Early Hits: " + str(early_hit), True, RED) 
    screen.blit(early, (500, 550))
    
    numOfMisses = total_beats - perfect_hit - good_hit - early_hit
    misses = font.render("Misses: " + str(numOfMisses), True, RED)
    screen.blit(misses, (500, 600))
    
    if (score/max_score) == 1:
        SS_rank.draw()
    elif (score/max_score) >= 0.95:
        S_rank.draw()
    elif (score/max_score) >= 0.88:
        A_rank.draw()
    elif (score/max_score) >= 0.8:
        B_rank.draw()
    elif (score/max_score) >= 0.7:
        C_rank.draw()
    else:
        D_rank.draw()
        
class imageScaling(): # scaling images, not original code (pulled from https://php.tbc.school.nz/12/neshan.upton/Mini%20Project%202/level_editor.py)
  def __init__(self, x, y, image, scale):
    width = image.get_width()
    height = image.get_height()
    self.image = pygame.transform.scale(
        image, (int(width * scale), int(height * scale)))
    self.rect = self.image.get_rect()
    self.rect.topleft = (x, y)

  def draw(self):
     screen.blit(self.image, (self.rect.x, self.rect.y))
     
SS_rank = imageScaling(800, 300, SS_rank, 4)
S_rank = imageScaling(800, 300, S_rank, 4)
A_rank = imageScaling(800, 300, A_rank, 4)
B_rank = imageScaling(800, 300, B_rank, 4)
C_rank = imageScaling(800, 300, C_rank, 4)
D_rank = imageScaling(800, 300, D_rank, 4)
hit_circle_object = imageScaling(605, 340, hit_circle, 1) # 65, 65 for reference

async def main():
    global beat_times, score, current_beat, last_hit, current_max_score, song_name, combo
    global total_beats, max_score, perfect_hit, good_hit, early_hit, max_combo, x_pos, y_pos
    global approach_radius, game_start, song_start, multi_click, game_over, hit_circle_object, cursor_img_rect
    
    # loading images

    osu_menu = pygame.image.load("assets/osumenu.jpg")
    osu_menu = imageScaling(0, 0, osu_menu, 1)

    song_bg = pygame.image.load("assets/" + song_name + ".jpg")
    song_bg = imageScaling(0, 0, song_bg, 1.05)

    song_choice_one = pygame.image.load("assets/Namikare.jpg")
    song_choice_one = imageScaling(1000, 80, song_choice_one, 0.1)

    song_choice_two = pygame.image.load("assets/Breaking the Habit.jpg")
    song_choice_two = imageScaling(1000, 200, song_choice_two, 0.1)

    song_choice_three = pygame.image.load("assets/Padoru.jpg")
    song_choice_three = imageScaling(1000, 330, song_choice_three, 0.15)

    song_choice_four = pygame.image.load("assets/Warriors.jpg")
    song_choice_four = imageScaling(1000, 440, song_choice_four, 0.15)

    song_choice_five = pygame.image.load("assets/Anoyo Iki no Bus.jpg")
    song_choice_five = imageScaling(1000, 560, song_choice_five, 0.1)

    run = True # game function to create window

    pygame.mouse.set_visible(False)
    cursor_img_rect = cursor_img.get_rect() # https://stackoverflow.com/questions/63369201/how-to-change-the-cursor-in-pygame-to-a-custom-image

    while run:
        if not game_over:
            if not game_start:
                screen.fill(BLACK)
                circle_hitbox = pygame.draw.circle(screen, GREEN, (640, 360), 250, width=5) # draws cursor
                osu_menu.draw()
                startText = font.render("Click osu! to begin!", True, WHITE) # instructional text
                screen.blit(startText, (30, 30))
                
                songSelectText = font.render("Song Selection!", True, WHITE) 
                screen.blit(songSelectText, (975, 25))
                
                song_choice_one.draw()
                song_choice_two.draw()
                song_choice_three.draw()
                song_choice_four.draw()
                song_choice_five.draw()
                
                cursor_img_rect.center = pygame.mouse.get_pos()  # update position 
                screen.blit(cursor_img, cursor_img_rect) # draw the cursor
                
            # if hover, will make green outline
            if circle_hitbox.collidepoint(pygame.mouse.get_pos()) and not game_start:
                circle_hitbox = pygame.draw.circle(screen, GREEN, (640, 360), 250, width=5)  
                
            if pygame.rect.Rect(1000, 80, 192, 108).collidepoint(pygame.mouse.get_pos()) and not song_start: 
                pygame.draw.rect(screen, GREEN, (1000, 80, 192, 108), 2)

            if pygame.rect.Rect(1000, 200, 192, 128).collidepoint(pygame.mouse.get_pos()) and not song_start: 
                pygame.draw.rect(screen, GREEN, (1000, 200, 192, 128), 2)

            if pygame.rect.Rect(1000, 328, 200, 108).collidepoint(pygame.mouse.get_pos()) and not song_start: 
                pygame.draw.rect(screen, GREEN, (1000, 328, 200, 108), 2)
                    
            if pygame.rect.Rect(1000, 440, 192, 108).collidepoint(pygame.mouse.get_pos()) and not song_start: 
                pygame.draw.rect(screen, GREEN, (1000, 440, 192, 108), 2)
                    
            if pygame.rect.Rect(1000, 560, 192, 108).collidepoint(pygame.mouse.get_pos()) and not song_start: 
                pygame.draw.rect(screen, GREEN, (1000, 560, 192, 108), 2)
                    
            if game_start: 
                start_song()
                pygame.time.set_timer(beat_event, round(beat_times[current_beat]*1000 - beat_times[current_beat - 1]*1000)) # first beat
                game_start = False
                song_start = True
                
            if song_start:
                draw_screen() # this runs 60 times per second because of clock.tick(60)

            for event in pygame.event.get(): # all events (including custom) are detected here
                #print(event)
                if event.type == pygame.QUIT: # exits game
                    run = False
                if event.type == pygame.KEYDOWN:
                    pass
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 or event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    x, y = event.pos
                    if not song_start and circle_hitbox.collidepoint(x, y): 
                        game_start = True
                    if not song_start and pygame.rect.Rect(1000, 80, 192, 108).collidepoint(x, y): # changes song 
                        song_name = "Namikare"
                        beat_times = song_tempo()
                        song_select_update()
                    if not song_start and pygame.rect.Rect(1000, 200, 192, 108).collidepoint(x, y):
                        song_name = "Breaking the Habit" 
                        beat_times = song_tempo()     
                        song_select_update()
                    if not song_start and pygame.rect.Rect(1000, 328, 200, 108).collidepoint(x, y):
                        song_name = "Padoru"
                        beat_times = song_tempo()
                        song_select_update()
                    if not song_start and pygame.rect.Rect(1000, 440, 192, 108).collidepoint(x, y):
                        song_name = "Warriors"
                        beat_times = song_tempo()
                        song_select_update()
                    if not song_start and pygame.rect.Rect(1000, 560, 192, 108).collidepoint(x, y):
                        song_name = "Anoyo Iki no Bus"
                        beat_times = song_tempo()
                        song_select_update()
                        
                    if pygame.draw.circle(screen, GREEN, (x_pos+65, y_pos+65), 64).collidepoint(x, y) and song_start: # updates score
                        if approach_radius >= 150 and not multi_click:
                            score += 1
                            combo += 1
                            early_hit += 1
                            multi_click = True
                            last_hit = "early"
                            pygame.mixer.Sound.play(hit_sound)
                        elif approach_radius >= 100 and not multi_click:
                            score += 2
                            combo += 1
                            good_hit += 1
                            multi_click = True
                            last_hit = "good"
                            pygame.mixer.Sound.play(hit_sound)
                        elif approach_radius >= 70 and not multi_click:
                            score += 3
                            combo += 1
                            perfect_hit += 1
                            last_hit = "perfect"
                            multi_click = True
                            pygame.mixer.Sound.play(hit_sound)

                if event.type == beat_event: 
                    # custom event is triggered whenever beat 
                    #print(current_beat)
                    #print(total_beats)

                    if not multi_click: # updates max_combo for score screen calculation
                        if combo >= max_combo:
                            max_combo = combo 
                        combo = 0
                        last_hit = "miss"
                    
                    x_pos = random.randint(305, 1105) # randomizes next circle position
                    y_pos = random.randint(225, 575)
                    hit_circle_object = imageScaling(x_pos, y_pos, hit_circle, 1)  # redraws hit circle
                    multi_click = False # resets multi_click
                    
                    approach_radius = 200 # sets radius back to 200 for next note
                    current_beat += 1 # sets next beat
                    current_max_score = 3*(current_beat - 1)
                    try: # try and except so game ends
                        miliseconds = round(beat_times[current_beat]*1000 - beat_times[current_beat - 1]*1000) # updates miliseconds between current beat and next beat
                    except: 
                        game_over = True
                    pygame.time.set_timer(beat_event, miliseconds) # next beat
                    
            if game_over: # draws game over, known to be buggy bc of text blit lagging
                song_bg.draw()
                score_tally()
                        
            pygame.display.update() # updates screen
            clock.tick(60) # every second at most 60 frames will be rendered
            
            await asyncio.sleep(0)
                
asyncio.run(main()) 