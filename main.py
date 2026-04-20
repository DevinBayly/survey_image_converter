import streamlit as st
import subprocess as sp

# have a file upload area
# have a button that converts it from e2c

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    with open("eq.png","wb") as f:
      f.write(bytes_data)
    sp.run(f"convert360 e2c eq.png cube.png --size 200",shell=True)
    with open("cube.png","rb") as f: 
      st.image("cube.png")
      st.download_button(
          label="Download cubemap",
          data=f,
          file_name="cube.png",
          mime="image/png",
          icon=":material/download:",
      ) 
# draw the image in the viewport 
# show a download button

