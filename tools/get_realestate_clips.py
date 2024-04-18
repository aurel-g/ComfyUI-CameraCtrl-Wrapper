import argparse
import json
import os
import os.path as osp
from tqdm import tqdm
from moviepy.editor import VideoFileClip
import imageio
from decord import VideoReader


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video_root', required=True)
    parser.add_argument('--save_path', required=True)
    parser.add_argument('--video2clip_json', required=True, help='generated by gather_realestate.py')
    parser.add_argument('--clip_txt_path', required=True, help='path to the downloaded realestate txt files')
    parser.add_argument('--low_idx', type=int, default=0, help='used for parallel processing')
    parser.add_argument('--high_idx', type=int, default=-1, help='used for parallel processing')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    os.makedirs(args.save_path, exist_ok=True)
    video2clips = json.load(open(args.video2clip_json, 'r'))
    video_names = list(video2clips.keys())[args.low_idx: args.high_idx] if args.high_idx != -1 else list(video2clips.keys())
    video2clips = {k: v for k, v in video2clips.items() if k in video_names}

    for video_name, clip_list in tqdm(video2clips.items()):
        video_path = osp.join(args.video_root, video_name + '.mp4')
        if not osp.exists(video_path):
            continue
        video = VideoFileClip(video_path)
        clip_save_path = osp.join(args.save_path, video_name)
        os.makedirs(clip_save_path, exist_ok=True)
        for clip in tqdm(clip_list):
            clip_save_name = clip + '.mp4'
            if osp.exists(osp.join(clip_save_path, clip_save_name)):
                continue
            with open(osp.join(args.clip_txt_path, clip + '.txt'), 'r') as f:
                lines = f.readlines()
            frames = [x for x in lines[1: ]]
            timesteps = [int(x.split(' ')[0]) for x in frames]
            if timesteps[-1] <= timesteps[0]:
                continue
            timestamps_seconds = [x / 1000000.0 for x in timesteps]
            frames = [video.get_frame(t) for t in timestamps_seconds]
            imageio.mimsave(osp.join(clip_save_path, clip_save_name), frames, fps=video.fps)
            video_reader = VideoReader(osp.join(clip_save_path, clip_save_name))
            assert len(video_reader) == len(timesteps)