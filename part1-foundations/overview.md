# Filosofía del laboratorio

Este manual se concibe como un laboratorio de investigación computacional. El objetivo no es únicamente ejecutar cálculos aislados, sino aprender a construir experimentos computacionales reproducibles que permitan explorar el espacio químico de manera sistemática.

El enfoque pedagógico sigue un modelo denominado **Semilla y Bosque**. Un cálculo individual constituye la semilla; la expansión sistemática de variantes genera el bosque de datos.

En la práctica, se espera que los estudiantes realicen primero un conjunto reducido de cálculos denominados *semilla*. Durante esta etapa se familiarizan con la estructura de los archivos de entrada y salida, la ejecución de los programas, la extracción de resultados y el análisis de propiedades moleculares.

Una vez comprendido este proceso básico, los resultados obtenidos pueden compararse con conjuntos de datos más amplios previamente preparados en este documento, el *bosque*. Este contraste permite analizar cómo los mismos cálculos, aplicados de manera sistemática a múltiples variantes de un sistema químico, generan información útil para la investigación y la resolución de problemas químicos reales.

De esta forma, el manual busca sustituir el tiempo que tradicionalmente se dedica a repetir cálculos individuales por un tiempo centrado en la interpretación de resultados obtenidos de forma masiva. Este enfoque se inspira en la transformación reciente de la investigación científica, donde la automatización computacional, la generación de grandes bases de datos y las herramientas de análisis asistidas por inteligencia artificial han modificado profundamente la manera en que se produce conocimiento.

En esencia, el manual propone un salto conceptual: desde el momento inicial en que un estudiante envía un cálculo individual, hasta el punto en que es capaz de analizar la información que emerge de un conjunto amplio de resultados generados mediante ese mismo procedimiento. El objetivo final no es únicamente aprender a realizar cálculos, sino comprender cómo estos pueden integrarse en flujos de trabajo que conduzcan a conocimiento químico.

```{admonition} Pipeline científico
:class: tip
cálculo individual → generación sistemática de variantes → construcción de dataset → análisis estadístico → interpretación química
```

## Pipelines científicos

La investigación moderna en química computacional se organiza mediante pipelines reproducibles. Un pipeline es una secuencia estructurada de operaciones que transforma una representación química inicial en información interpretable.

```{admonition} Ejemplo de pipeline
:class: tip
representación molecular → generación de estructuras → cálculo de propiedades → extracción de descriptores → análisis multivariado
```

Cada bloque del manual introduce herramientas que permiten construir pipelines cada vez más complejos. Al final del curso el estudiante es capaz de ensamblar varios pipelines para resolver problemas de investigación.

## Metodología de las prácticas

Cada práctica se desarrolla en tres etapas.

### Cálculo semilla

Caracterización detallada de un sistema modelo para comprender el fenómeno químico y validar el nivel de teoría.

### Expansión del sistema

Generación automatizada de múltiples variantes mediante scripts y enumeración sistemática de sustituyentes, metales o condiciones.

### Análisis

Construcción de un dataset y análisis mediante correlaciones químicas, modelos estadísticos o métodos de aprendizaje automático.
