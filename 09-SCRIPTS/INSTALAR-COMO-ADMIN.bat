@echo off
REM UMOE OS 8.0 - Instalar agendamento diario
REM Execute este arquivo como ADMINISTRADOR (botao direito -> Executar como administrador)

echo.
echo  UMOE OS 8.0 - Instalando Pipeline Agendado...
echo  ================================================

set PYTHON=C:\Users\andrei.elastico\AppData\Local\Programs\Python\Python312\python.exe
set SCRIPT=C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\01-AGENTE-AUTONOMO\umoe-pipeline.py
set WORKDIR=C:\01 - UMOE\09 - IA\umoe-os-8
set TASKNAME=UMOE_Pipeline_Master

REM Remover tarefa antiga se existir
schtasks /delete /tn "%TASKNAME%" /f 2>nul

REM Criar nova tarefa - Seg a Sex as 10:00
schtasks /create /tn "%TASKNAME%" ^
  /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
  /sc weekly /d MON,TUE,WED,THU,FRI ^
  /st 10:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

if %errorlevel% == 0 (
  echo.
  echo  OK! Tarefa instalada com sucesso.
  echo  Nome:    %TASKNAME%
  echo  Agenda:  Seg-Sex as 10:00
  echo  Script:  %SCRIPT%
  echo.
  echo  Verificando proxima execucao:
  schtasks /query /tn "%TASKNAME%" /fo list
) else (
  echo.
  echo  ERRO ao instalar. Execute como ADMINISTRADOR.
)

echo.
pause
