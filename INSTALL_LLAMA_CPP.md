# Hướng dẫn cài đặt llama-cpp-python

## Vấn đề

`llama-cpp-python` cần C++ compiler để build từ source code. Trên Windows, bạn cần Visual Studio Build Tools.

## Giải pháp

### Cách 1: Cài Visual Studio Build Tools (Khuyến nghị)

1. **Tải Visual Studio Build Tools:**
   - Truy cập: https://visualstudio.microsoft.com/downloads/
   - Chọn "Build Tools for Visual Studio 2022"
   - Tải file installer

2. **Cài đặt:**
   - Chạy installer
   - Chọn các thành phần sau:
     - ✅ **Desktop development with C++**
     - ✅ **Windows 10 SDK** hoặc **Windows 11 SDK**
     - ✅ **C++ CMake tools**

3. **Sau khi cài xong:**
   ```bash
   cd D:\Projects\EnglishApp
   .\venv\Scripts\python.exe scripts\install_llama_cpp.py
   ```

   Hoặc chạy trực tiếp:
   ```bash
   cd D:\Projects\EnglishApp
   $env:FORCE_CMAKE="1"
   $env:CMAKE_ARGS="-DGGML_CUDA=OFF"
   .\venv\Scripts\python.exe -m pip install llama-cpp-python
   ```

### Cách 2: Sử dụng script tự động

Chạy script đã tạo sẵn:
```bash
cd D:\Projects\EnglishApp
.\venv\Scripts\python.exe scripts\install_llama_cpp.py
```

Script sẽ:
- Kiểm tra xem có C++ compiler không
- Nếu có: Tự động cài llama-cpp-python
- Nếu không: Hiển thị hướng dẫn và mở trang download

## Lưu ý

- **Ứng dụng vẫn chạy được** mà không cần llama-cpp-python
- Chỉ **Writing tab** (sử dụng Phi-3) sẽ không hoạt động
- Các tab khác vẫn hoạt động bình thường:
  - ✅ Vocab
  - ✅ Speaking (có faster-whisper)
  - ✅ YouTube
  - ✅ News
  - ✅ Grammar
  - ✅ Exam
  - ✅ Settings

## Kiểm tra sau khi cài

```bash
.\venv\Scripts\python.exe -m pip list | Select-String llama-cpp-python
```

Nếu thấy `llama-cpp-python` trong danh sách là đã cài thành công!

