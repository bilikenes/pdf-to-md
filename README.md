# **Local PDF to Markdown** 

A Windows application that converts PDF files to Markdown entirely on your computer using <u><mark>`pymupdf4llm`</mark></u> <mark>.</mark> Your files are never uploaded to a web service. 

## **Getting Started** 

1. Make sure Python 3.10 or later is installed on your computer. 

2. Double-click <mark>`run.bat` .</mark> 

3. On the first launch, the required packages will be installed in a local <mark>`.venv`</mark> directory. Subsequent launches will start the application directly. 


4. Drag and drop your PDF files into the application window, **Convert to Markdown**

## **Default Settings** 

By default, the application: 

- Runs OCR automatically when needed. 
- Uses <mark>`tur+eng`</mark> as the OCR language. 
- Excludes headers and footers from the output. 

- Saves the <mark>`.md`</mark> file in the same directory as the source PDF. 
- Never overwrites an existing Markdown file. If a file with the same name already exists, a suffix such as <mark>`_2`</mark> or <mark>`_3`</mark> is added automatically. 

## **OCR** 

Text-based PDFs usually do not require OCR. 

For scanned PDFs, the application uses PyMuPDF4LLM's OCR support. If Turkish OCR does not work, you may need to install Tesseract OCR and the Turkish language data package ( `tur` ) on your system. 

To disable OCR completely, select **Do not use OCR** in the application settings. 

## **Building the Windows Application** 

Double-click <mark>`build.bat`</mark> to create the packaged application. 

After the build process is complete, the executable will be available at: 

```
# **Local PDF to Markdown** 

A Windows application that converts PDF files to Markdown entirely on your computer using <u><mark>`pymupdf4llm`</mark></u> <mark>.</mark> Your files are never uploaded to a web service. 

## **Getting Started** 

1. Make sure Python 3.10 or later is installed on your computer. 

2. Double-click <mark>`run.bat` .</mark> 

3. On the first launch, the required packages will be installed in a local <mark>`.venv`</mark> directory. Subsequent launches will start the application directly. 


4. Drag and drop your PDF files into the application window, **Convert to Markdown**

## **Default Settings** 

By default, the application: 

- Runs OCR automatically when needed. 
- Uses <mark>`tur+eng`</mark> as the OCR language. 
- Excludes headers and footers from the output. 

- Saves the <mark>`.md`</mark> file in the same directory as the source PDF. 
- Never overwrites an existing Markdown file. If a file with the same name already exists, a suffix such as <mark>`_2`</mark> or <mark>`_3`</mark> is added automatically. 

## **OCR** 

Text-based PDFs usually do not require OCR. 

For scanned PDFs, the application uses PyMuPDF4LLM's OCR support. If Turkish OCR does not work, you may need to install Tesseract OCR and the Turkish language data package ( `tur` ) on your system. 

To disable OCR completely, select **Do not use OCR** in the application settings. 

## **Building the Windows Application** 

Double-click <mark>`build.bat`</mark> to create the packaged application. 

After the build process is complete, the executable will be available at: 

```
dist\PDF-to-Markdown\PDF-to-Markdown.exe
```

The application is packaged as a directory-based build instead of a single executable to provide faster startup times. 

When copying or distributing the application, move the entire directory: 

### `dist\PDF-to-Markdown` 

Do not copy only the <mark>`.exe`</mark> file. 

## **Privacy** 

PDF conversion is performed entirely on your computer. 

The application does not contain: 

- Network requests 

- Cloud-based processing 

- Artificial intelligence API integrations 

- File uploads to external services 

An internet connection is only required during the initial setup, when Python packages are downloaded and installed. Once installation is complete, PDF conversion works locally. 

