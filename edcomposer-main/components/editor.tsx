"use client";

import { Player } from "@remotion/player";
import { useState } from "react";
import { remotionConfig } from "@/config/remotion";
import { edcomposerConfig } from "@/remotion/AIVideoGen";
import { useRender } from "@/hooks/useRender";
import "./editor.css";

export default function Editor() {
  const {
    start: startRender,
    status: renderStatus,
    progressPercent,
  } = useRender({
    onSuccess: (url) => {
      (window as any).open(url);
    },
  });

  const [prompt, setPrompt] = useState("");

  return (
    // CHANGED HTML STRUCTURE AND ADDED CLASSES
    <div className="flex flex-col gap-2 items-stretch w-full">
      <div className="editor-page-content">
        <div className="content">
          <div className="logo"></div>

          {/* Ask for prompt */}
          <h1>
            What do you wanna <span>learn</span> about?
          </h1>
          <div className="topic-input-container">
            <p className="teach-me">Teach me </p>
            <input
              placeholder="Write down a topic"
              className="topic-input"
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <button className="add-button button">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 18 18"
                fill="none"
              >
                <path
                  d="M18 10.2857H10.2857V18H7.71429V10.2857H0V7.71429H7.71429V0H10.2857V7.71429H18V10.2857Z"
                  fill="#9E62EF"
                />
              </svg>
              Add More
            </button>
          </div>

          <textarea
            className="extra-input"
            placeholder="Add more details"
          ></textarea>

          <div className="loader">
            <div className="loading-bar">
              <div style={{
                width: 0
              }} className="current-progress"></div>
            </div>

            <button className="cancel-button">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="4"
                viewBox="0 0 18 4"
                fill="none"
              >
                <path
                  d="M18 3.28566H10.2857H7.71429H0V0.714233H7.71429H10.2857H18V3.28566Z"
                  fill="white"
                />
                <path
                  d="M18 3.28566H10.2857H7.71429H0V0.714233H7.71429H10.2857H18V3.28566Z"
                  fill="url(#paint0_linear_17_64)"
                />
                <defs>
                  <linearGradient
                    id="paint0_linear_17_64"
                    x1="18"
                    y1="1.99995"
                    x2="-0.383722"
                    y2="1.99995"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop stop-color="#ED6868" />
                    <stop offset="0.520833" stop-color="#F38B8B" />
                    <stop offset="1" stop-color="#ED6868" />
                  </linearGradient>
                </defs>
              </svg>
              Cancel
            </button>
          </div>
        </div>

        <div className="video-player flex w-full h-full grow">
          <div className="pre-render">
            <button className="render-button button">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
              >
                <path
                  d="M6.25005 4.66663L4.16672 5.83329L5.33338 3.74996L4.16672 1.66663L6.25005 2.83329L8.33338 1.66663L7.16672 3.74996L8.33338 5.83329L6.25005 4.66663ZM16.25 12.8333L18.3334 11.6666L17.1667 13.75L18.3334 15.8333L16.25 14.6666L14.1667 15.8333L15.3334 13.75L14.1667 11.6666L16.25 12.8333ZM18.3334 1.66663L17.1667 3.74996L18.3334 5.83329L16.25 4.66663L14.1667 5.83329L15.3334 3.74996L14.1667 1.66663L16.25 2.83329L18.3334 1.66663ZM11.1167 10.65L13.15 8.61663L11.3834 6.84996L9.35005 8.88329L11.1167 10.65ZM11.975 6.07496L13.925 8.02496C14.25 8.33329 14.25 8.87496 13.925 9.19996L4.20005 18.925C3.87505 19.25 3.33338 19.25 3.02505 18.925L1.07505 16.975C0.750049 16.6666 0.750049 16.125 1.07505 15.8L10.8 6.07496C11.125 5.74996 11.6667 5.74996 11.975 6.07496Z"
                  fill="#9E62EF"
                />
              </svg>
              Render your video
            </button>
          </div>
          <Player
            controls
            clickToPlay
            inputProps={{ prompt }}
            component={edcomposerConfig.component as any}
            compositionHeight={1080}
            compositionWidth={1920}
            fps={remotionConfig.fps}
            durationInFrames={edcomposerConfig?.durationInFrames ?? 100}
            style={{
              width: "100%",
              height: "100%",
              aspectRatio: 9 / 16,
              backgroundColor: "#000",
            }}
            className="post-render"
          />
        </div>
        {/* <button
        disabled={renderStatus !== 'ready'}
        onClick={() =>
          startRender({
            inputProps: {
              prompt
            },
            compId: 'edcomposer'
          })
        }
      >
        Render: {renderStatus} {progressPercent && `${progressPercent}%`}
      </button> */}
      </div>
    </div>
  );
}
