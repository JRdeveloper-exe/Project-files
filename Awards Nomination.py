albums = []
nominations = []
total = 0
artist = input("Please enter Artist of choice: ")
#print(artist.upper())

while True:
    album = input("Please enter album name (Press s to stop): ")
    if album.lower() == "s":
        break
    else:
        nomination = float(input(f"Please Enter the number of nominations of the album {album}: "))
        albums.append(album)
        nominations.append(nomination)
print(f"----- {artist}-----")

for album in albums:
    print(f"{album}_ _ _ _          {nomination}")

for nomination in nominations:
    total += nomination
    
print(f"Total nomination in carreer:     {total}")