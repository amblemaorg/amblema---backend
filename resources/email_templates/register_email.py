from flask import current_app


def messageRegisterEmail(email, password):
    return """
<!DOCTYPE html
PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title></title>
  <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700&display=swap" rel="stylesheet">
  <style>

    .row {
      display: -webkit-box;
      display: -ms-flexbox;
      display: flex;
      -ms-flex-wrap: wrap;
      flex-wrap: wrap;
      margin-right: -15px;
      margin-left: -15px;
    }

    body {
      font-family: 'Montserrat', sans-serif !important;
      margin: 0;
      padding: 0;
      min-width: 100%;
      background-color: #ffffff;
    }

    table {
      border-spacing: 0;
      padding-right: 0 !important;
      padding-left: 0 !important;
    }

    td {
      padding: 0;
    }

    .outer {
      margin: 0 auto;
      width: 100%;
      padding-top: 4rem;
      padding-bottom: 4rem;
      padding-right: 2rem;
      padding-left: 2rem;
    }

    .justify-content-center {
      justify-content: center;
    }

    .main-bg {
      background-position: center;
      background-repeat: no-repeat;
      background-size: contain;
      background-image: url(http://157.245.131.248:10506/resources/images/mailing/register-background.png);
    }

    .title-welcome {
      font-size: 1.3rem !important;
      color: #008096;
      width: 100%;
      font-weight: 700 !important;
      margin-top: 1.5rem;
      margin-bottom: 1.2rem;
      text-align: center;
    }

    .wrapper {
      padding-top: : 0rem;
      position: relative;
    }
    .title-wrapper {
      margin: 0rem 0rem 0rem 0rem;
    }

    .credentials-wrapper {
      margin: 2rem 0rem 2rem 0rem;
    }
    .middle-wrapper {
      margin: 1rem 0.5rem 1rem 0.5rem;
    }
    .bottom-wrapper {
      margin: 1rem 3rem 1rem 3rem;
    }

    .center {
      margin: 0;
      position: absolute;
      top: 45%;
      left: 50%;
      -ms-transform: translate(-50%, -50%);
      transform: translate(-50%, -50%);
    }

    .text {
      color: #008096;
      font-size: 0.7rem !important;
      text-align: center;
      font-weight: 700;
    }

    .text-2 {
      color: #008096;
      font-size: 0.9rem !important;
      text-align: center;
      font-weight: 700;
      margin-top: 0px;
      margin-bottom: 0px;
    }

    .text-3 {
      color: #008096;
      font-size: 0.7rem !important;
      text-align: center;
      font-weight: 700;
      margin-top: 0px;
      margin-bottom: 0px;
    }

    @media (min-width: 0px) {
      .outer {
        max-width: auto;
      }
      .main-bg {
        background-size: contain;
        min-height: 20em !important;
      }
      .wrapper {
        margin-top: 2rem;
      }
      .bottom-wrapper {
        margin: 1rem 0.5rem 1rem 0.5rem;
      }
    }

    @media (min-width: 576px) {

      .main-bg {
        background-size: contain;
        min-height: 30em !important;
      }
      .text-3 {
        font-size: 1rem !important;
      }
      .text-2 {
        font-size: 1.2rem !important;
      }
      .text {
        font-size: 1rem !important;
      }
    }

    @media (min-width: 768px) {

      .outer {
        max-width: auto !important;
      }

      .main-bg {
        background-size: contain;
        max-width: 100% !important;
        height: auto !important;
        width: 100%
      }
      .text-3 {
        font-size: 1rem !important;
      }
      .text-2 {
        font-size: 1.1rem !important;
      }
      .text {
        font-size: 1rem !important;
      }

      .center {
        top: 40%;
        left: 45%;
        -ms-transform: translate(-40%, -50%);
        transform: translate(-40%, -50%);

      }

      .title-welcome {
        font-size: 1.5rem !important;
      }
      
    }

    @media (min-width: 992px) {
      .outer {
        max-width: 992px;
      }

      .main-bg {
        background-size: contain;
        min-height: 40em !important;
        max-width: 992px !important;
      }
      .text-3 {
        font-size: 1rem !important;
      }
      .text-2 {
        font-size: 1.1rem !important;
      }
      .text {
        font-size: 1rem !important;
      }

      .center {
        top: 47%;
        left: 45%;
        -ms-transform: translate(-40%, -50%);
        transform: translate(-40%, -50%);

      }

      .title-welcome {
        font-size: 2rem !important;
      }
    }

    @media (min-width: 0px) and (max-width: 767px) {
      #mobile-content { display: block; }
      #desktop-content { display: none; }
      #main-bg-desktop { background-image: none; }
    }

    @media (min-width: 768px){
      #mobile-content { display: none; }
      #desktop-content { display: block; }
      #main-bg-mobile { background-image: none; }
    }
  </style>
</head>

<body>
  <center>
    <table id="main-bg-desktop" class="outer main-bg" width="100%">
      <tr>
        <td style="width: 100%;">
          <div class="columns">
            <div id="mobile-content">
              <h3 id="title-mobile" class="title-welcome title-wrapper">¡Bienvenido a AmbLeMa!</h3>
              <p class="text middle-wrapper">Estamos emocionados de que hayas decidido formar parte de Fundación AmbLeMa.
                  Inicia la experiencia de ser parte de AmbLema completando algunos pasos.
                  Para ello ingresa a nuestra página con las siguientes credenciales:
              </p>
              <div class="justify-content-center credentials-wrapper">
                <p class="text-2">Usuario: """+email+"""</p>
                <p class="text-2">Contraseña: """+password+"""</p>
              </div>
            </div>
            <div id="main-bg-mobile" class="wrapper main-bg">
              <div class="center">
                <div id="desktop-content">
                  <h3 id="title-mobile" class="title-welcome title-wrapper">¡Bienvenido a AmbLeMa!</h3>
                  <p class="text middle-wrapper">Estamos emocionados de que hayas decidido formar parte de Fundación AmbLeMa.
                      Inicia la experiencia de ser parte de AmbLema completando algunos pasos.
                      Para ello ingresa a nuestra página con las siguientes credenciales:
                  </p>
                  <div class="justify-content-center credentials-wrapper">
                    <p class="text-2">Usuario: """+email+"""</p>
                    <p class="text-2">Contraseña: """+password+"""</p>
                  </div>
                </div>
                <div class="justify-content-center bottom-wrapper">
                  <p class="text">Si quieres contactar con nuestro equipo, no dudes en hacerlo a través de info@amblema.org</p>
                </div>
                <div class="justify-content-center">
                  <p class="text-3">Ten un excelente día</p>
                  <p class="text-3">Fundación AmbLeMa</p> 
                </div>
              </div>
            </div>
          </div>
        </td>
      </tr>

    </table>
  </center>
</body>

</html>
                """
