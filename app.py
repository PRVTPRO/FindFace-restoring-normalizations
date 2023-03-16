import requests
import os
import json
import logging


def collector(ip, token, rootdir):

    print("Number of dossiers to range [0,1,2,3...dossiers count]")
    dossiers = int(input())
    print("Save source_photo [0] or thumbnail [1] ?")
    print("0 - Saves the original photo")
    print("1 - Saves the thumbnail photo (Only cropped photos will be saved, solves the problem if there are a lot of faces in the photo)")
    source_type = int(input())

    logging.basicConfig(filename='error_collector.log',
                        encoding='utf-8', level=logging.ERROR)

    url = f"http://{ip}/objects/faces/"

    headers = {
        "accept": "application/json",
        "Authorization": f"Token {token}"
    }
    logging.info('Collector started')
    for dossier_id in range(dossiers):

        params = {"dossier": dossier_id}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            # обрабатываем полученные данные
            if data['next_page'] == None:
                print(
                    f"[Sourcr] Dossier {dossier_id} count objects face  {data['count']}")
                for el in data['results']:
                    folder_name = f"{rootdir}/" + str(dossier_id)
                    if not os.path.exists(folder_name):
                        os.makedirs(folder_name)

                    with open(f"{folder_name}/{el['id']}.txt", "w") as outfile:
                        json.dump(el, outfile)

                    # Проверяем, что файл существует и его размер больше нуля
                    if os.path.exists(f"{folder_name}/{el['id']}.txt") and os.stat(f"{folder_name}/{el['id']}.txt").st_size > 0:
                        print(
                            f"{folder_name}/{el['id']}.txt useful data was successfully saved.")
                    else:
                        print(
                            f"ERROR: {folder_name}/{el['id']}.txt useful data was not saved.")
                        quit()

                    if source_type == 0:
                        source_photo = requests.get(
                            el['source_photo'], stream=True)
                    else:
                        source_photo = requests.get(
                            el['thumbnail'], stream=True)

                    if source_photo.status_code == 200:
                        with open(f"{folder_name}/{el['id']}.jpg", "wb") as f:
                            f.write(source_photo.content)
                            print(
                                f"ID face {el['id']} saved to the dossier folder {folder_name}")

                    else:
                        print(
                            f"Photo upload error {el['id']}.jpg, dossier {dossier_id}")
                        logging.error(
                            f"Photo upload error  {el['id']}.jpg, dossier {dossier_id}")

            else:
                print("next_page is not None (many attachment pages)- Exit")
                logging.error(
                    "next_page is not None (many attachment pages)- Exit")
                quit()
        else:
            data = response.json()
            if data['desc'] == f"Select a valid choice. {dossier_id} is not one of the available choices.":
                print(
                    f"Dossier with ID {dossier_id} missing in the system, Request error: {response.status_code} {data['code']} ")
            else:
                print(f"Critical error: {data}")
                logging.error(f"Critical error: {data}")
    logging.info('Collector End')


def add_face(ip, token, rootdir):

    logging.basicConfig(filename='err_add_face.log',
                        encoding='utf-8', level=logging.ERROR)

    url = f"http://{ip}/objects/faces/"
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {token}",
    }
    data = {
        'mf_selector': 'reject',
        'active': 'true',
    }


    for subdir, dirs, files in os.walk(rootdir):
        for filename in files:
            if filename.endswith('.jpg'):
                dossier = os.path.basename(subdir)
                file_path = os.path.join(subdir, filename)
                files_data = {
                    'source_photo': (filename, open(file_path, 'rb'), 'image/jpeg')
                }
                data['dossier'] = int(dossier)
                response = requests.post(
                    url, headers=headers, data=data, files=files_data)
                data = response.json()
                if response.status_code == 201:
                    print(f"Фото {filename} загружено в досье {dossier}")
                else:
                    print(
                        f"Critical add photo ID {filename}: Dossier ID: {dossier} Описание {data['desc']}")
                    logging.error(
                        f"Critical add photo ID {filename}: Dossier ID: {dossier} Описание {data['desc']}")


def remove_face(ip, token, rootdir):

    logging.basicConfig(filename='err_remove_face.log',
                        encoding='utf-8', level=logging.ERROR)

    for subdir, dirs, files in os.walk(rootdir):
        for filename in files:
            if filename.endswith('.jpg'):
                dossier = os.path.basename(subdir)
                file_path = os.path.join(subdir, filename)
                name, ext = os.path.splitext(filename)
                url = f"http://{ip}/objects/faces/{name}/"
                headers = {
                    "accept": "application/json",
                    "Authorization": f"Token {token}",
                }

                response = requests.delete(url, headers=headers)
                if response.status_code == 204:
                    print(f"Face {filename} removed from the dossier{dossier}")
                else:
                    data = response.json()
                    print(
                        f"Critical delete photo ID {filename}: Dossier ID: {dossier} Desc: {data['desc']}")
                    logging.error(
                        f"Critical add photo ID {filename}: Dossier ID: {dossier} Desc: {data['desc']}")


print("IP address FindFace server")
ip = input()

print("Auth token for FindFace server, only token")
token = input()

print("Dir name for working with the dossier")
rootdir = input()

print("Select the function to run:")
print("[1] Collector: we form a local copy of the full photos from the dossier with the preservation of the folder structure")
print("[2] Add_face: adding local photos to the photo dossier by folder name")
print("[3] Remove_face: using the local file structure, we delete old photos from the dossier")

run_def = int(input())
if run_def == 1:
    # we form a local copy of the full photos from the dossier with the preservation of the folder structure
    collector(ip, token, rootdir)
elif run_def == 2:
    # adding local photos to the photo dossier by folder name
    add_face(ip, token, rootdir)
elif run_def == 3:
    # using the local file structure, we delete old photos from the dossier
    remove_face(ip, token, rootdir)
else:
    print("Bye")
