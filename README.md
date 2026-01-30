# 🧠 Smart Study Assistant

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688.svg)
![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **Course:** BSAI301 Software Engineering  
> **Team:** team-10



## 📖 Project Overview (项目概览)

**Smart Study Assistant** 是一个基于 AI 的智能学习辅助平台，旨在帮助大学生解决信息过载问题。系统允许用户上传课程录音（MP3）或阅读材料（PDF），利用大语言模型自动生成**内容摘要**、**关键知识点**以及**复习闪卡 (Flashcards)**。

通过将非结构化数据转化为结构化的复习工具，本项目旨在提升学生的复习效率和知识留存率。

### ✨ Key Features (核心功能)
- 📂 **多格式支持**: 支持 PDF 文档解析与 MP3/WAV 音频转写。
- 🤖 **AI 智能摘要**: 基于 OpenAI/LLM 自动提取核心内容与待办事项。
- 🗂️ **自动生成闪卡**: 根据笔记内容自动生成 "Q&A" 复习卡片。
- ⚡ **异步处理**: 采用 Celery + Redis 架构，支持后台处理大型文件，无需用户长时间等待。
- 📊 **学习仪表盘**: 追踪上传历史与复习状态。

---

## 🏗️ System Architecture (系统架构)

本项目采用前后端分离架构，并引入消息队列以解耦耗时的 AI 推理任务。

```mermaid
graph TD
    User([User]) -->|Browser| Client[Frontend (React + Tailwind)]
    Client -->|REST API| API[Backend (FastAPI)]
    
    subgraph Infrastructure
        API -->|Read/Write| DB[(PostgreSQL)]
        API -->|Enqueue Task| Redis[(Redis Broker)]
    end
    
    subgraph Async Worker
        Redis -->|Consume Task| Worker[Celery Worker]
        Worker -->|Call LLM| OpenAI[OpenAI API]
        Worker -->|Save Result| DB
    end
