import os
import shutil
import xml.etree.ElementTree as ET
import sys
import re

def standardize_media(target_dir):
    if not os.path.isdir(target_dir):
        print(f"Error: {target_dir} is not a valid directory.")
        return

    print(f"Standardizing media for: {target_dir}")

    # Define standardized structure
    media_root = os.path.join(target_dir, "media")
    
    media_dirs = {
        "fanart": os.path.join(media_root, "fanart"),
        "cover": os.path.join(media_root, "cover"),
        "logo": os.path.join(media_root, "logo"),
        "video": os.path.join(media_root, "video")
    }

    for d in media_dirs.values():
        os.makedirs(d, exist_ok=True)

    # 1. First, move all files based on naming patterns
    # (Suffix, target_subdir)
    mappings = {
        "-image": "fanart",
        "-thumb": "cover",
        "-marquee": "logo",
        "-video": "video"
    }

    # Helper to move and rename
    def process_dir(source_subdir, suffix_mapping):
        source_path = os.path.join(target_dir, source_subdir)
        if not os.path.exists(source_path):
            return

        for filename in os.listdir(source_path):
            full_source = os.path.join(source_path, filename)
            if not os.path.isfile(full_source):
                continue

            base, ext = os.path.splitext(filename)
            for suffix, target_key in suffix_mapping.items():
                if base.endswith(suffix):
                    new_base = base[:-len(suffix)]
                    new_filename = new_base + ext
                    target_dir_path = media_dirs[target_key]
                    full_target = os.path.join(target_dir_path, new_filename)
                    
                    print(f"Moving: {source_subdir}/{filename} -> media/{target_key}/{new_filename}")
                    try:
                        shutil.move(full_source, full_target)
                    except Exception as e:
                        print(f"Error: {e}")
                    break
            else:
                # Special case: if it doesn't match suffix but is in a folder, 
                # maybe it should be moved anyway if it matches a game? 
                # For now, let's handle the specific case of 'halflife.jpg' if it's in images/
                if source_subdir == "images":
                    # If it's just {jogo}.ext, where should it go?
                    # In ES, usually just {jogo}.ext in images/ is treated as 'image' (fanart)
                    new_filename = filename
                    full_target = os.path.join(media_dirs["fanart"], new_filename)
                    print(f"Moving non-suffixed: images/{filename} -> media/fanart/{new_filename}")
                    try:
                        shutil.move(full_source, full_target)
                    except Exception as e:
                        print(f"Error: {e}")

    # Process images and videos
    process_dir("images", {suffix: key for suffix, key in mappings.items() if key != "video"})
    process_dir("videos", {"-video": "video"})

    # 2. Update gamelist.xml
    gamelist_path = os.path.join(target_dir, "gamelist.xml")
    if os.path.exists(gamelist_path):
        print("Updating gamelist.xml...")
        try:
            tree = ET.parse(gamelist_path)
            root = tree.getroot()

            for game in root.findall("game"):
                # Tag to folder mapping
                tag_map = {
                    "image": "fanart",
                    "thumbnail": "cover",
                    "marquee": "logo",
                    "video": "video"
                }

                for tag, folder in tag_map.items():
                    node = game.find(tag)
                    if node is not None and node.text:
                        path_text = node.text.strip().replace("\\", "/")
                        # We want to change any images/... or videos/... to media/folder/...
                        # And strip any suffix like -image, -thumb, etc if they exist in the text path
                        
                        # Rule-based replacement
                        filename = os.path.basename(path_text)
                        base, ext = os.path.splitext(filename)
                        
                        # Strip suffix if it matches the expected one for the tag
                        suffix_to_strip = {
                            "image": "-image",
                            "thumbnail": "-thumb",
                            "marquee": "-marquee",
                            "video": "-video"
                        }.get(tag, "")

                        if base.endswith(suffix_to_strip):
                            new_base = base[:-len(suffix_to_strip)]
                        else:
                            new_base = base
                        
                        new_path = f"./media/{folder}/{new_base}{ext}"
                        if node.text != new_path:
                            node.text = new_path

            # Indent and save
            indent(root)
            tree.write(gamelist_path, encoding="utf-8", xml_declaration=True)
            print("Done! gamelist.xml optimized.")

        except Exception as e:
            print(f"Error updating gamelist.xml: {e}")

    # Clean up empty folders
    for d in ["images", "videos"]:
        p = os.path.join(target_dir, d)
        if os.path.exists(p) and not os.listdir(p):
            print(f"Removing empty directory: {d}")
            os.rmdir(p)

def indent(elem, level=0):
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python standardize_media.py <folder_path>")
    else:
        standardize_media(sys.argv[1])
