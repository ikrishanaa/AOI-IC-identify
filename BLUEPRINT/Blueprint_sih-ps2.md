

# **Automated Optical Inspection (AOI) System for Integrated Circuit Marking: A Software Architecture and Implementation Blueprint**

## **High-Level System Architecture & Design Philosophy**

This document provides a definitive architectural blueprint for an industry-grade Automated Optical Inspection (AOI) system designed for the verification of Integrated Circuit (IC) markings. The architecture is engineered for high availability, scalability, and robust data integrity, supporting two primary operational modes: **Batch Image Analysis** for high-throughput offline inspection and **Live Stream Analysis** for real-time, continuous monitoring on the production line.

### **MVP vs. Long-Term Architecture: A Note on Feasibility**

To ensure credibility and a clear path to execution, particularly within a hackathon context, it is vital to distinguish between the Minimum Viable Product (MVP) and the full, long-term architecture.

* **The MVP (Hackathon Scope):** The immediate goal is to demonstrate the core value proposition. This subset will focus on the **Batch Image Analysis** workflow. It will implement a simplified, two-signal pipeline (OCR and Logo Identification via a cloud API) and a basic, rule-based Decision Engine. The architecture will be streamlined, potentially combining services into a more monolithic structure for rapid deployment, while proving the end-to-end concept of "image in, verdict out."  
* **The Long-Term Architecture:** The complete design detailed in this document represents the production-ready system. It includes the full microservices architecture, both Batch and Live Stream analysis modes, the complete four-signal AI pipeline (including Visual Signature and Anomaly Detection), and a sophisticated, configurable Decision Engine. This robust architecture is the target for post-hackathon development and is designed for industrial-scale deployment.

This document describes the long-term architecture, but the implementation plan should prioritize the MVP components first.

### **System Overview and Architectural Diagram**

The system is designed as a collection of decoupled, independently deployable microservices. This approach ensures fault tolerance and scalability, which are paramount in a production setting.1 The system supports two distinct workflows:

1\. Batch Image Analysis Workflow (Asynchronous):  
This workflow is optimized for processing large quantities of static images with high reliability and data persistence.

1. **Request Initiation:** An operator uploads one or more IC images via the Next.js frontend.  
2. **Job Registration:** The request is routed to the **Inspection Management Service**, which creates a job record in the PostgreSQL database, publishes a task to the Redis message broker, and immediately returns a job\_id.  
3. **Asynchronous Multi-Signal Processing:** A **Celery Worker** picks up the task and executes the full multi-signal verification pipeline: ROI detection, OCR, logo identification, visual signature analysis, and surface anomaly detection.3  
4. **Decision & Persistence:** The worker passes all collected evidence to the **Decision Engine Service** for a final verdict. The complete results and evidence are then persisted to the database.  
5. **Result Retrieval:** The frontend polls a status endpoint using the job\_id and displays the detailed results once the job is complete.

2\. Live Stream Analysis Workflow (Real-Time):  
This workflow is designed for low-latency, continuous inspection of a live video feed from a production line camera.

1. **Stream Connection:** The Next.js frontend establishes a WebSocket connection with the backend and requests a live video feed from the new **Stream Ingestion & Processing Service**.5  
2. **Video Ingestion:** The Stream Ingestion Service connects to a camera's RTSP feed using OpenCV and begins capturing frames.7  
3. **Real-Time Frame Processing:** For each captured frame, the service executes the same multi-signal verification pipeline in a non-blocking thread.10 To maintain low latency, it makes synchronous calls to the **Component Verification Service** and **Decision Engine Service**.  
4. **Pushing Results:** The analysis results for each frame (verdict, bounding boxes, OCR text) are immediately pushed to the frontend via the WebSocket connection.11  
5. **Live Visualization:** The frontend receives the data and renders it as a dynamic overlay on top of the live video feed, providing immediate visual feedback to the operator.  
6. **Event Capture (Optional):** The operator can trigger a "capture event" from the UI, which instructs the backend to save the current frame and its analysis results to the PostgreSQL database for auditing and later review, using the same persistence logic as the batch workflow.

This dual-workflow architecture is illustrated in the diagram below.

\!([https://i.imgur.com/8Q6Vp6E.png](https://i.imgur.com/8Q6Vp6E.png))

### **Core Architectural Tenets: Asynchronous, Event-Driven Microservices**

The selection of a microservices architecture is a deliberate engineering decision driven by the fundamental requirements of an industrial application. The system employs two distinct communication patterns tailored to its operational modes:

* **Asynchronous, Message-Based (for Batch Processing):** The core function of processing static images is a computationally intensive and time-variable process, classified as a "long-running task".3 For this mode, an asynchronous, message-based pattern using Celery and Redis is non-negotiable.3 This ensures reliability (tasks persist in the queue even if a worker fails) and scalability (worker pools can be scaled independently to handle load).  
* **Real-Time, Stream-Based (for Live Analysis):** For continuous inspection, low latency is the primary concern. This mode bypasses the message queue and uses a direct, persistent connection via WebSockets.6 A dedicated service ingests the video stream and processes frames as they arrive, pushing results immediately to the client. This pattern minimizes overhead and provides the instantaneous feedback required for on-the-fly monitoring.15

The design adheres to the principles of Domain-Driven Design (DDD), where each microservice is aligned with a specific business capability, promoting high cohesion and loose coupling.

### **Technology Stack Justification**

The technology stack was selected to support the core architectural tenets of high performance, asynchronicity, and maintainability.

* **FastAPI (Backend):** Chosen for its high performance, native async/await support, and built-in WebSocket and StreamingResponse capabilities, making it ideal for both REST APIs and real-time video streaming.14  
* **Next.js (Frontend):** A leading React framework that provides a rich development experience, flexible data fetching, and the ability to handle real-time data streams via WebSockets for dynamic UI updates.5  
* **PostgreSQL (Database):** A powerful, open-source object-relational database known for its reliability, feature robustness, and strong support for data integrity and complex queries, including JSONB for flexible data storage.17 The pgvector extension will be utilized for efficient similarity searches on feature embeddings.  
* **Celery & Redis (Task Queue):** Celery is the industry standard for distributed task queues in Python. When paired with Redis as a fast, in-memory message broker, it provides the essential infrastructure for managing long-running asynchronous batch jobs.  
* **Docker (Containerization):** Docker allows each microservice to be packaged with its dependencies into a portable container, ensuring consistency across development, testing, and production environments and simplifying deployment.18

The following table provides a clear contract of responsibilities for each backend service.

| Service Name | Core Responsibility | Primary Technologies | Key Dependencies | Communication Patterns |
| :---- | :---- | :---- | :---- | :---- |
| **API Gateway** | Route requests; handle authentication, rate limiting, WebSocket connections. | FastAPI, Uvicorn | All backend services | Synchronous (HTTP Proxy), WebSocket Proxy |
| **Inspection Management Service** | Manage the lifecycle of batch inspection jobs; publish tasks. | FastAPI, Uvicorn, Celery Client | PostgreSQL, Redis | Synchronous (API), Asynchronous (Task Publishing) |
| **Batch Processing Service** | Execute the multi-signal pipeline for static images (asynchronous). | Celery, OpenCV, Tesseract | Redis, PostgreSQL, Verification & Decision Services | Asynchronous (Task Consumption), Synchronous (Internal API Calls) |
| **Stream Ingestion & Processing Service** | Ingest and process live video streams (real-time). | FastAPI, OpenCV, WebSockets | Verification & Decision Services | Real-Time (RTSP In, WebSocket Out) |
| **Component Verification Service** | Validate OCR output via Nexar API or datasheet parsing. | FastAPI, Uvicorn, GraphQL Client | Nexar API, PostgreSQL (Cache) | Synchronous (API) |
| **Decision Engine Service** | Apply configurable rules to evidence signals to compute a final verdict. | FastAPI, Uvicorn | None | Synchronous (API) |

## **AI & Computer Vision Pipeline**

The core of this system is a multi-signal verification pipeline that moves beyond simple OCR to create a layered, high-confidence verification process. By synthesizing multiple independent signals, the system becomes far more resilient to sophisticated counterfeits where one attribute (like text) might be correct, but others (like the logo font or surface texture) are not.

### **Visual Explainability Diagram**

The following diagram illustrates the flow of data from a single input image through the various analysis stages to a final, synthesized verdict.

\!(([https://i.imgur.com/jY8wZ6s.png](https://i.imgur.com/jY8wZ6s.png)))

### **Detailed Pipeline Stages**

1. **Image Preprocessing:** This is the foundational step for all subsequent analyses. A robust, adaptive pipeline is crucial for handling real-world image defects like poor lighting, glare, and skew, which are common on reflective IC surfaces.30 The pipeline includes:  
   * **Scaling:** Ensuring the image resolution is at least 300 DPI, as OCR performance degrades significantly below this threshold.32  
   * **Deskewing:** Correcting the rotational angle of the text to be horizontal.  
   * **Contrast Enhancement:** Using Contrast Limited Adaptive Histogram Equalization (CLAHE) to sharpen character edges without blowing out highlights.  
   * **Adaptive Binarization:** Converting the image to black and white using a method like Otsu's thresholding, which is robust against uneven lighting.30  
   * **Noise Removal:** Applying filters to remove sensor noise and artifacts.  
2. **Region of Interest (ROI) Detection:** After cleaning the image, the system localizes the specific areas containing the text and the manufacturer's logo.  
   * **Text ROI:** OpenCV's EAST (Efficient and Accurate Scene Text) detector, a deep learning model, is used to identify and draw bounding boxes around text regions.  
   * **Logo ROI:** For the MVP, a simple template matching or a pre-trained lightweight object detection model (e.g., YOLO) can be used to find the logo.  
3. **Signal 1: Optical Character Recognition (OCR):** The cropped text ROI is passed to the Tesseract OCR engine. This step extracts the raw alphanumeric string (part number, date codes, etc.) from the component's surface.  
4. **Signal 2: Logo Identification:** The logo ROI is processed to identify the manufacturer, providing a critical cross-verification signal.  
   * **Primary Method (Cloud API):** For the highest accuracy with minimal setup (ideal for a hackathon), the logo ROI is sent to a commercial vision API like Google Cloud Vision or AWS Rekognition. These services use powerful, pre-trained models to recognize a vast number of corporate logos.  
   * **Fallback Method (Local Model):** For the long-term architecture, a custom, lightweight Convolutional Neural Network (CNN) is trained on a dataset of common electronic manufacturer logos. This provides an offline, cost-effective alternative to the cloud API.  
5. **Signal 3: Visual Signature Analysis:** This advanced technique verifies authenticity by analyzing the *style* of the marking, not just its content. It is highly effective at detecting counterfeits that have the correct text but use the wrong font, spacing, or layout.  
   * **Process:** A pre-trained CNN (e.g., ResNet) is used as a feature extractor to convert the text ROI into a high-dimensional feature vector, or "embedding". This embedding numerically represents the visual characteristics of the marking.  
   * **Comparison:** This vector is then compared against a database of pre-computed embeddings from "golden sample" images of genuine components using cosine similarity. A high similarity score indicates a strong visual match, while a low score flags a potential fake.  
6. **Signal 4: Surface Anomaly Detection:** This signal targets physical tampering, such as "blacktopping" (resurfacing a chip to apply new markings) or using incorrect engraving methods.  
   * **Method:** An unsupervised learning model, specifically an **autoencoder**, is trained exclusively on images of genuine, defect-free components.  
   * **Detection:** When a new image is processed, the autoencoder attempts to reconstruct it. If the component has been tampered with, its surface texture will differ from the training data, resulting in a high "reconstruction error." This high error score serves as the anomaly signal.  
7. **Synthesis in Decision Engine:** All of the collected signals—the OCR'd text, the predicted logo, the visual similarity score, and the surface anomaly score—are aggregated. This full evidence package is then passed to the **Decision Engine Service**, which applies a weighted, rule-based logic to compute a final, high-confidence verdict.

## **Backend Microservice Implementation**

This section provides the detailed implementation blueprint for each backend microservice.

### **API Gateway Service (FastAPI)**

The API Gateway serves as the unified entry point. It will handle request routing for both standard HTTP requests and WebSocket connections, abstracting the internal service network from the client.

### **Inspection Management Service (FastAPI)**

This service orchestrates the **batch image analysis** workflow. Its API is non-blocking, returning a task identifier immediately upon job submission.12

* **Pydantic Models & API Endpoints:** (Unchanged from previous version)

### **Batch Processing Service (Celery Worker)**

This is the computational core for **batch processing**, implemented as a set of Celery tasks. It operates independently, consuming tasks from the Redis queue.3

* **Celery Task Definition (tasks.py):** (Unchanged from previous version, logic remains focused on the multi-signal pipeline for a single image job).

### **Stream Ingestion & Processing Service (FastAPI)**

This new service is the heart of the **live analysis** workflow. It is responsible for connecting to a live camera feed, processing frames in real-time, and streaming results to the frontend.

* **Responsibilities:**  
  * **Video Ingestion:** Connect to an IP camera using its RTSP stream URL via cv2.VideoCapture.7 To avoid blocking I/O, frame reading will be handled in a separate thread.10  
  * **Real-Time Processing:** For each frame, it will execute the full multi-signal verification pipeline. This reuses the same logic modules as the Celery worker but runs them synchronously within a processing loop to minimize latency.  
  * **Result Streaming:** It will manage WebSocket connections, pushing a JSON payload with the analysis results (verdict, coordinates, scores) for each processed frame to the connected client(s).6  
  * **Video Feed Streaming:** It will expose a separate HTTP endpoint that provides a StreamingResponse with multipart/x-mixed-replace content type, allowing the raw video feed to be displayed in a simple \<img\> tag on the frontend.15  
* **API Endpoints:**

| HTTP Method | Endpoint Path | Description | Success Response |
| :---- | :---- | :---- | :---- |
| GET | /live/feed | Provides a continuous multipart/x-mixed-replace stream of video frames for browser display. | 200 OK \- StreamingResponse |
| WebSocket | /ws/live/analysis | Establishes a WebSocket for pushing real-time analysis JSON data for each frame. | WebSocket Connection |

### **Component Verification Service (FastAPI)**

(Unchanged from previous version, includes Nexar API integration and datasheet parsing fallback).

### **Decision Engine Service (FastAPI)**

(Unchanged from previous version, responsible for applying rules to compute the final verdict).

### **Final API Response Contract**

(Unchanged from previous version, the JSON structure for a single inspection result remains the same for both batch and captured live events).

## **Frontend Application Blueprint (Next.js)**

The frontend application is updated to support both batch processing and the new live analysis mode.

### **Project and Code Structure**

(Unchanged from previous version, follows modern Next.js best practices with a src/ directory and feature-based organization).23

### **Core User Interfaces and Workflows**

The frontend design now includes a dedicated interface for real-time monitoring.

* **Dashboard (/), New Inspection Page (/new), Job Status Viewer (/inspections/\[job\_id\]):** These pages remain dedicated to the batch processing workflow, centered around the "submit and poll" pattern.  
* **New Live Analysis Page (/live):** This new page provides the interface for continuous, real-time inspection.  
  * **UI Components:** It will feature a large video player area and a side panel for controls and logs.  
  * **Video Feed:** The video player will display the live camera feed by setting the src of an \<img\> tag to the /api/live/feed endpoint on the backend.  
  * **WebSocket Connection:** On page load, the component establishes a WebSocket connection to the /ws/live/analysis endpoint.5  
  * **Real-Time Overlays:** The component will listen for incoming messages on the WebSocket. Each message will contain a JSON payload with the analysis for a single frame. The frontend will use this data to dynamically render overlays (e.g., bounding boxes around ICs, text labels with the OCR result, and color-coded verdict indicators) directly on top of the video feed.  
  * **Event Capture:** A "Save Snapshot" button will be available. When clicked, it sends a message over the WebSocket to the backend, instructing it to persist the current frame and its analysis data to the database. This creates a permanent record of a specific event identified during live monitoring.

## **Data Persistence and Auditing (PostgreSQL)**

The database schema remains largely the same, but its usage is clarified for the two operational modes.

### **PostgreSQL Database Schema**

* **Schema Definition:** (Unchanged from previous version, includes inspection\_jobs, inspection\_results, reference\_components, etc.).  
* **Data Persistence Logic:**  
  * **Batch Mode:** Every uploaded image and its full analysis result are saved to the inspection\_jobs and inspection\_results tables.  
  * **Live Mode:** Analysis results are **not** saved to the database by default to maintain low latency and avoid overwhelming the database. Data is only persisted when an operator explicitly triggers a "Save Snapshot" event from the frontend. This action creates a new record in the database as if it were a single batch submission, ensuring critical events are captured for audit and review.

### **Immutable Audit Trail Implementation**

(Unchanged from previous version, continues to use the robust "shadow table with triggers" approach for all persisted records).25

## **Deployment and Operational Guide**

The deployment configuration is updated to include the new real-time streaming service.

### **Detailed Project Structure**

This project tree provides a complete and unabridged blueprint for organizing the codebase. It separates the backend and frontend concerns while promoting modularity and maintainability within each part of the application.28

aoi-ic-marking/  
├──.github/  
│   └── workflows/  
│       └── ci.yml             \# GitHub Actions workflow for CI/CD  
├──.gitignore  
├── docker-compose.yml         \# Main docker-compose for all services  
├── README.md  
│  
├── backend/  
│   ├──.env.example           \# Example environment variables for backend services  
│   ├── Dockerfile             \# Single Dockerfile for all Python services  
│   ├── requirements.txt       \# All Python dependencies (FastAPI, Celery, OpenCV, etc.)  
│   │  
│   ├── api\_gateway/  
│   │   ├── \_\_init\_\_.py  
│   │   └── main.py            \# FastAPI app for the API Gateway (routing, auth)  
│   │  
│   ├── decision\_engine/  
│   │   ├── \_\_init\_\_.py  
│   │   └── main.py            \# FastAPI app for the Decision Engine service  
│   │  
│   ├── inspection\_service/  
│   │   ├── \_\_init\_\_.py  
│   │   └── main.py            \# FastAPI app for Batch Inspection Management  
│   │  
│   ├── batch\_processing\_service/ \# Celery worker for the batch processing pipeline  
│   │   ├── \_\_init\_\_.py  
│   │   ├── celery\_app.py      \# Celery app instantiation  
│   │   └── tasks.py           \# Celery task definitions (process\_inspection\_image)  
│   │  
│   ├── stream\_ingestion\_service/ \# New service for live feed  
│   │   ├── \_\_init\_\_.py  
│   │   └── main.py            \# FastAPI app for Stream Ingestion & Processing  
│   │  
│   ├── verification\_service/  
│   │   ├── \_\_init\_\_.py  
│   │   └── main.py            \# FastAPI app for Component Verification  
│   │  
│   ├── shared/                \# Shared code used by multiple backend services  
│   │   ├── \_\_init\_\_.py  
│   │   ├── db.py              \# Database connection and session management  
│   │   ├── models.py          \# Pydantic models for API contracts  
│   │   ├── schemas.py         \# SQLModel/SQLAlchemy table definitions  
│   │   └── utils.py           \# Common utility functions  
│   │  
│   └── tests/  
│       ├── \_\_init\_\_.py  
│       ├── test\_inspection\_service.py  
│       ├── test\_batch\_processing\_service.py  
│       └── conftest.py        \# Pytest fixtures and configuration  
│  
└── frontend/  
    ├── public/                \# Static assets (images, fonts)  
    │   ├── favicon.ico  
    │   └── logo.svg  
    ├── src/  
    │   ├── app/               \# Next.js App Router  
    │   │   ├── (main)/        \# Route group for main application layout  
    │   │   │   ├── layout.tsx \# Main layout (e.g., with sidebar/header)  
    │   │   │   ├── page.tsx   \# Dashboard homepage for batch jobs  
    │   │   │   ├── new/  
    │   │   │   │   └── page.tsx \# New batch inspection submission page  
    │   │   │   ├── live/      \# New route for live analysis  
    │   │   │   │   └── page.tsx \# Live analysis dashboard page  
    │   │   │   └── inspections/  
    │   │   │       └── \[job\_id\]/  
    │   │   │           └── page.tsx \# Job status and results viewer for batch jobs  
    │   │   └── (auth)/        \# Route group for authentication pages  
    │   │       ├── login/  
    │   │       │   └── page.tsx  
    │   │       └── layout.tsx  
    │   │  
    │   ├── components/        \# Global, reusable UI components \[23\]  
    │   │   ├── ui/            \# Primitives like Button.tsx, Card.tsx, Input.tsx  
    │   │   └── icons/         \# Icon components  
    │   │  
    │   ├── features/          \# Feature-based modules \[23\]  
    │   │   ├── inspection-dashboard/  
    │   │   │   ├── components/  
    │   │   │   │   └── JobListTable.tsx  
    │   │   │   └── hooks/  
    │   │   │       └── useRecentJobs.ts  
    │   │   ├── job-submission/  
    │   │   │   └── components/  
    │   │   │       └── ImageDropzone.tsx  
    │   │   ├── results-viewer/  
    │   │   │   ├── components/  
    │   │   │   │   ├── ResultDisplay.tsx  
    │   │   │   │   └── EvidenceCard.tsx  
    │   │   │   └── hooks/  
    │   │   │       └── useJobStatus.ts  
    │   │   └── live-viewer/  
    │   │       ├── components/  
    │   │       │   ├── VideoPlayer.tsx  
    │   │       │   └── LiveOverlay.tsx  
    │   │       └── hooks/  
    │   │           └── useLiveAnalysis.ts  
    │   │  
    │   ├── lib/               \# Library code, API clients, utils \[23\]  
    │   │   ├── api.ts         \# Configured client for backend API calls  
    │   │   ├── websocket.ts   \# WebSocket connection management  
    │   │   └── utils.ts       \# General utility functions  
    │   │  
    │   └── styles/  
    │       └── globals.css    \# Global CSS styles  
    │  
    ├──.env.local.example  
    ├── next.config.js  
    ├── package.json  
    ├── tailwind.config.ts  
    └── tsconfig.json

### **Containerization with Docker and Docker Compose**

The docker-compose.yml file is updated to include the new stream\_ingestion\_service.

* **Unified Backend Dockerfile:** (Unchanged, a single Dockerfile is still used for all Python services).29  
* **Updated Docker Compose Configuration (docker-compose.yml):**  
  YAML  
  version: '3.8'

  services:  
    \# \-- DATABASE \--  
    postgres:  
      image: postgres:15-alpine  
      volumes:  
        \- postgres\_data:/var/lib/postgresql/data/  
      environment:  
        \- POSTGRES\_USER=user  
        \- POSTGRES\_PASSWORD=password  
        \- POSTGRES\_DB=aoi\_db  
      ports:  
        \- "5432:5432"  
      healthcheck:  
        test:  
        interval: 10s  
        timeout: 5s  
        retries: 5

    redis:  
      image: redis:7-alpine  
      ports:  
        \- "6379:6379"  
      healthcheck:  
        test:  
        interval: 10s  
        timeout: 5s  
        retries: 5

    \# \-- BACKEND SERVICES \--  
    inspection\_service:  
      build:  
        context:./backend  
      command: uvicorn inspection\_service.main:app \--host 0.0.0.0 \--port 8000 \--reload  
      volumes:  
        \-./backend:/app  
      ports:  
        \- "8001:8000"  
      depends\_on:  
        postgres:  
          condition: service\_healthy  
        redis:  
          condition: service\_healthy  
      environment:  
        \- DATABASE\_URL=postgresql://user:password@postgres/aoi\_db  
        \- CELERY\_BROKER\_URL=redis://redis:6379/0  
        \- CELERY\_RESULT\_BACKEND=redis://redis:6379/0

    batch\_worker: \# Renamed from 'worker' for clarity  
      build:  
        context:./backend  
      command: celery \-A batch\_processing\_service.celery\_app worker \--loglevel=info  
      volumes:  
        \-./backend:/app  
      depends\_on:  
        postgres:  
          condition: service\_healthy  
        redis:  
          condition: service\_healthy  
      environment:  
        \- DATABASE\_URL=postgresql://user:password@postgres/aoi\_db  
        \- CELERY\_BROKER\_URL=redis://redis:6379/0  
        \- CELERY\_RESULT\_BACKEND=redis://redis:6379/0  
        \- NEXAR\_API\_KEY=${NEXAR\_API\_KEY}

    stream\_ingestion\_service: \# New service definition  
      build:  
        context:./backend  
      command: uvicorn stream\_ingestion\_service.main:app \--host 0.0.0.0 \--port 8000 \--reload  
      volumes:  
        \-./backend:/app  
      ports:  
        \- "8002:8000" \# Expose on a different host port  
      depends\_on:  
        postgres:  
          condition: service\_healthy  
      environment:  
        \- DATABASE\_URL=postgresql://user:password@postgres/aoi\_db  
        \- NEXAR\_API\_KEY=${NEXAR\_API\_KEY}

    \#... (definitions for api\_gateway, verification\_service, and decision\_engine would be similar)

    \# \-- FRONTEND SERVICE \--  
    frontend:  
      build:  
        context:./frontend  
      volumes:  
        \-./frontend:/app  
        \- /app/node\_modules  
        \- /app/.next  
      ports:  
        \- "3000:3000"  
      environment:  
        \- NEXT\_PUBLIC\_API\_URL=http://localhost:8001 \# Or gateway URL

  volumes:  
    postgres\_data:

### **CI/CD and Production Deployment Strategy**

(Unchanged from previous version, continues to recommend a Kubernetes-based deployment for production environments to manage scaling, health checks, and zero-downtime updates).18

## **Future Scope**

While the MVP focuses on core functionality, the long-term vision for this platform includes several innovative extensions to further enhance its capabilities:

* Integration with BharatNet / factory PLC systems for automation triggers.  
* Add GAN-based fake marking synthesis to generate fake data for model training.  
* Integrate LLM-based reasoning for anomaly explanations (“Logo font mismatch detected; possible fake batch”).  
* Predictive failure analysis — linking fake ICs to field test failures.

## **Conclusion**

This document has outlined a comprehensive, dual-mode software architecture for an Automated Optical Inspection system. By clearly distinguishing between an achievable hackathon MVP and the robust long-term vision, this plan provides a credible and actionable roadmap.

The MVP, focused on batch image analysis with a two-signal pipeline, will prove the core concept. The full architecture evolves this into a production-grade system with both asynchronous **Batch Image Analysis** and real-time **Live Stream Analysis**. The core multi-signal verification pipeline—incorporating OCR, logo identification, visual signature analysis, and surface anomaly detection—creates a layered defense that is far more resilient to sophisticated counterfeits.

This updated blueprint provides a clear path for developing a sophisticated, reliable, and feature-rich AOI system that addresses the full spectrum of inspection needs—from high-volume batch verification to immediate, real-time quality control.

#### **Works cited**

1. Microservice pattern example. FastAPI as an entrypoint, RabbitMQ as a broker and python services \- GitHub, accessed October 15, 2025, [https://github.com/laricko/microservices-example](https://github.com/laricko/microservices-example)  
2. Building a Machine Learning Microservice with FastAPI | NVIDIA Technical Blog, accessed October 15, 2025, [https://developer.nvidia.com/blog/building-a-machine-learning-microservice-with-fastapi/](https://developer.nvidia.com/blog/building-a-machine-learning-microservice-with-fastapi/)  
3. Managing Background Tasks and Long-Running Operations in FastAPI | Leapcell, accessed October 15, 2025, [https://leapcell.io/blog/managing-background-tasks-and-long-running-operations-in-fastapi](https://leapcell.io/blog/managing-background-tasks-and-long-running-operations-in-fastapi)  
4. Asynchronous Tasks with FastAPI and Celery, accessed October 15, 2025, [https://www.nashruddinamin.com/blog/asynchronous-tasks-with-fastapi-and-celery](https://www.nashruddinamin.com/blog/asynchronous-tasks-with-fastapi-and-celery)  
5. Building Real-Time Applications with WebSockets and Next.js | by @rnab | Sep, 2025, accessed October 15, 2025, [https://arnab-k.medium.com/building-real-time-applications-with-websockets-and-next-js-e8d799b80440](https://arnab-k.medium.com/building-real-time-applications-with-websockets-and-next-js-e8d799b80440)  
6. WebSockets \- FastAPI, accessed October 15, 2025, [https://fastapi.tiangolo.com/advanced/websockets/](https://fastapi.tiangolo.com/advanced/websockets/)  
7. god233012yamil/Building-a-FastAPI-Web-Server-to-Stream-Video-from-Camera \- GitHub, accessed October 15, 2025, [https://github.com/god233012yamil/Building-a-FastAPI-Web-Server-to-Stream-Video-from-Camera](https://github.com/god233012yamil/Building-a-FastAPI-Web-Server-to-Stream-Video-from-Camera)  
8. god233012yamil/How-to-Stream-a-Camera-Using-OpenCV-and-Threads \- GitHub, accessed October 15, 2025, [https://github.com/god233012yamil/How-to-Stream-a-Camera-Using-OpenCV-and-Threads](https://github.com/god233012yamil/How-to-Stream-a-Camera-Using-OpenCV-and-Threads)  
9. IP camera stream using RTSP and openCV python \- YouTube, accessed October 15, 2025, [https://www.youtube.com/watch?v=6wI6tzRogZQ](https://www.youtube.com/watch?v=6wI6tzRogZQ)  
10. Multithreading with OpenCV-Python to improve video processing performance, accessed October 15, 2025, [https://nrsyed.com/2018/07/05/multithreading-with-opencv-python-to-improve-video-processing-performance/](https://nrsyed.com/2018/07/05/multithreading-with-opencv-python-to-improve-video-processing-performance/)  
11. FastAPI & OpenCV: A Comprehensive Guide to Real-Time Face Detection | by Sam Akan, accessed October 15, 2025, [https://medium.com/@samakan061/fastapi-opencv-a-comprehensive-guide-to-real-time-face-detection-c12779295f16](https://medium.com/@samakan061/fastapi-opencv-a-comprehensive-guide-to-real-time-face-detection-c12779295f16)  
12. Handling Long-Running Jobs in FastAPI with Celery & RabbitMQ | by mrcompiler \- Medium, accessed October 15, 2025, [https://medium.com/@mrcompiler/handling-long-running-jobs-in-fastapi-with-celery-rabbitmq-9c3d72944410](https://medium.com/@mrcompiler/handling-long-running-jobs-in-fastapi-with-celery-rabbitmq-9c3d72944410)  
13. Asynchronous Patterns for Microservice Communication | Bits and Pieces \- Bit.dev, accessed October 15, 2025, [https://blog.bitsrc.io/asynchronous-patterns-for-microservice-communication-edd6722a7323](https://blog.bitsrc.io/asynchronous-patterns-for-microservice-communication-edd6722a7323)  
14. FastAPI Streaming Response: Unlocking Real-Time API Power \- Apidog, accessed October 15, 2025, [https://apidog.com/blog/fastapi-streaming-response/](https://apidog.com/blog/fastapi-streaming-response/)  
15. Low Latency Video Streaming Application with FastApi \- Medium, accessed October 15, 2025, [https://medium.com/@praveen06061995/low-latency-video-streaming-application-with-fastapi-4c69f5124fda](https://medium.com/@praveen06061995/low-latency-video-streaming-application-with-fastapi-4c69f5124fda)  
16. Seeking Optimization for Video Streaming Route in FastAPI \- Facing Slowness Issue \#10104 \- GitHub, accessed October 15, 2025, [https://github.com/fastapi/fastapi/discussions/10104](https://github.com/fastapi/fastapi/discussions/10104)  
17. Microservice in Python using FastAPI \- DEV Community, accessed October 15, 2025, [https://dev.to/paurakhsharma/microservice-in-python-using-fastapi-24cc](https://dev.to/paurakhsharma/microservice-in-python-using-fastapi-24cc)  
18. FastAPI for Scalable Microservices: Best Practices & Optimisation \- Webandcrafts, accessed October 15, 2025, [https://webandcrafts.com/blog/fastapi-scalable-microservices](https://webandcrafts.com/blog/fastapi-scalable-microservices)  
19. Dockerizing a FastAPI Backend and Next.js Frontend (Part 1\) | by Manjurul Hoque Rumi, accessed October 15, 2025, [https://medium.com/@manzurulhoque/dockerizing-a-fastapi-backend-and-next-js-frontend-part-1-configuring-kubernetes-part-2-920432d1f35f](https://medium.com/@manzurulhoque/dockerizing-a-fastapi-backend-and-next-js-frontend-part-1-configuring-kubernetes-part-2-920432d1f35f)  
20. Handling Long-Running Tasks in FastAPI, Best Practices and Strategies | DataScienceTribe, accessed October 15, 2025, [https://www.datasciencebyexample.com/2023/08/26/handling-long-running-tasks-in-fastapi-python/](https://www.datasciencebyexample.com/2023/08/26/handling-long-running-tasks-in-fastapi-python/)  
21. Faster video file FPS with cv2.VideoCapture and OpenCV \- PyImageSearch, accessed October 15, 2025, [https://pyimagesearch.com/2017/02/06/faster-video-file-fps-with-cv2-videocapture-and-opencv/](https://pyimagesearch.com/2017/02/06/faster-video-file-fps-with-cv2-videocapture-and-opencv/)  
22. Streaming video with FastAPI \- Petr Stribny, accessed October 15, 2025, [https://stribny.name/posts/fastapi-video/](https://stribny.name/posts/fastapi-video/)  
23. The Battle-Tested NextJS Project Structure I Use in 2025\. | by ..., accessed October 15, 2025, [https://medium.com/@burpdeepak96/the-battle-tested-nextjs-project-structure-i-use-in-2025-f84c4eb5f426](https://medium.com/@burpdeepak96/the-battle-tested-nextjs-project-structure-i-use-in-2025-f84c4eb5f426)  
24. Realtime Dashboard with FastAPI, Streamlit and Next.js \- Part 1 Data Producer, accessed October 15, 2025, [https://jaehyeon.me/blog/2025-02-18-realtime-dashboard-1/](https://jaehyeon.me/blog/2025-02-18-realtime-dashboard-1/)  
25. 3 Postgres Audit Methods: How to Choose? \- Satori, accessed October 15, 2025, [https://satoricyber.com/postgres-security/postgres-audit/](https://satoricyber.com/postgres-security/postgres-audit/)  
26. Database design for audit logging \[closed\] \- Stack Overflow, accessed October 15, 2025, [https://stackoverflow.com/questions/2015232/database-design-for-audit-logging](https://stackoverflow.com/questions/2015232/database-design-for-audit-logging)  
27. Best design for a changelog / auditing database table? \[closed\] \- Stack Overflow, accessed October 15, 2025, [https://stackoverflow.com/questions/201527/best-design-for-a-changelog-auditing-database-table](https://stackoverflow.com/questions/201527/best-design-for-a-changelog-auditing-database-table)  
28. Looking for the Octopart API?, accessed October 15, 2025, [https://octopart.com/business/api/v4/api-transition](https://octopart.com/business/api/v4/api-transition)  
29. FastAPI-PostgreSQL-Celery-RabbitMQ-Redis backend with Docker containerization \- Reddit, accessed October 15, 2025, [https://www.reddit.com/r/FastAPI/comments/nshn5b/fastapipostgresqlceleryrabbitmqredis\_backend\_with/](https://www.reddit.com/r/FastAPI/comments/nshn5b/fastapipostgresqlceleryrabbitmqredis_backend_with/)  
30. 7 steps of image pre-processing to improve OCR using Python \- NextGen Invent, accessed October 15, 2025, [https://nextgeninvent.com/blogs/7-steps-of-image-pre-processing-to-improve-ocr-using-python-2/](https://nextgeninvent.com/blogs/7-steps-of-image-pre-processing-to-improve-ocr-using-python-2/)  
31. image processing to improve tesseract OCR accuracy \- Stack Overflow, accessed October 15, 2025, [https://stackoverflow.com/questions/9480013/image-processing-to-improve-tesseract-ocr-accuracy](https://stackoverflow.com/questions/9480013/image-processing-to-improve-tesseract-ocr-accuracy)  
32. Improve OCR Accuracy with Preprocessing Tips | Docparser, accessed October 15, 2025, [https://docparser.com/blog/improve-ocr-accuracy/](https://docparser.com/blog/improve-ocr-accuracy/)