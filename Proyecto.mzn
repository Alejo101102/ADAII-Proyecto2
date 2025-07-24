% Parámetros del problema
int: num_personas;                                    
int: num_opiniones;                                   
array[1..num_opiniones] of int: distribucion_inicial; 
array[1..num_opiniones] of float: valores_extremismo; 
array[1..num_opiniones] of float: costos_extra;      
array[1..num_opiniones] of array[1..num_opiniones] of float: matriz_costos; 
float: costo_maximo;                                  
int: movimientos_maximos;

% Variables de decisión
array[1..num_opiniones, 1..num_opiniones] of var 0..num_personas: x;

% Variables auxiliares para el cálculo de costos y restricciones
array[1..num_opiniones] of var 0..num_personas: personas_finales; % distribución final de personas
var float: costo_total;                                           % costo total de la solución
var int: movimientos_totales;                                     % movimientos totales realizados
var float: extremismo_final;                                      % extremismo final de la población

% Restricciones

% 1. Conservación de personas: cada persona sale de exactamente una opinión
constraint forall(i in 1..num_opiniones)(
    sum(j in 1..num_opiniones)(x[i,j]) = distribucion_inicial[i]
);

% 2. Cálculo de la distribución final de personas
constraint forall(j in 1..num_opiniones)(
    personas_finales[j] = sum(i in 1..num_opiniones)(x[i,j])
);

% 3. Los movimientos de una opinión a sí misma están permitidos (representan personas que no se mueven)
constraint forall(i in 1..num_opiniones)(
    x[i,i] >= 0
);

% 4. Cálculo del costo total
constraint costo_total = sum(i in 1..num_opiniones, j in 1..num_opiniones where i != j)(
    % Costo base: c[i,j] * (1 + p[i]/n) * x[i,j]
    matriz_costos[i][j] * (1.0 + int2float(distribucion_inicial[i]) / int2float(num_personas)) * int2float(x[i,j]) +
    % Costo extra: si p[j] = 0 (opinión j estaba vacía), se suma ce[j] * x[i,j]
    (if distribucion_inicial[j] = 0 then costos_extra[j] * int2float(x[i,j]) else 0.0 endif)
);

% 5. Restricción de costo máximo
constraint costo_total <= costo_maximo;

% 6. Cálculo del número total de movimientos 
% Un movimiento de opinión i a opinión j cuenta como |j - i| movimientos
constraint movimientos_totales = sum(i in 1..num_opiniones, j in 1..num_opiniones where i != j)(
    abs(j - i) * x[i,j]
);

% 7. Restricción de movimientos máximos
constraint movimientos_totales <= movimientos_maximos;

% 8. Cálculo del extremismo final
constraint extremismo_final = sum(i in 1..num_opiniones)(
    int2float(personas_finales[i]) * valores_extremismo[i]
);

% 9. Restricción adicional: garantizar solución factible sin movimientos
constraint costo_total >= 0.0;
constraint movimientos_totales >= 0;

% Función objetivo: minimizar el extremismo final
solve minimize extremismo_final;

% Salida
output [
    "Extremismo inicial: " ++ show(sum(i in 1..num_opiniones)(int2float(distribucion_inicial[i]) * valores_extremismo[i])) ++ "\n",
    "Extremismo final: " ++ show(extremismo_final) ++ "\n",
    "Costo total: " ++ show(costo_total) ++ "\n",
    "Movimientos totales: " ++ show(movimientos_totales) ++ "\n",
    "Distribución inicial: " ++ show(distribucion_inicial) ++ "\n",
    "Distribución final: " ++ show(personas_finales) ++ "\n",
    "\nMovimientos realizados:\n"
] ++
[
    if fix(x[i,j]) > 0 then
        "De opinión " ++ show(i) ++ " a opinión " ++ show(j) ++ ": " ++ show(x[i,j]) ++ " personas\n"
    else ""
    endif
    | i in 1..num_opiniones, j in 1..num_opiniones where i != j
] ++
["\nMatriz de movimientos x[i,j]:\n"] ++
[
    if j = 1 then "[" else "" endif ++
    show(x[i,j]) ++
    if j = num_opiniones then "]\n" else ", " endif
    | i in 1..num_opiniones, j in 1..num_opiniones
];