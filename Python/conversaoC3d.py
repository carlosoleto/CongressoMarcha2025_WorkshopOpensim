import opensim as osim
import numpy as np
import os
from utils import rotate_data_table, mm_to_m, plot_sto_file
from utils import lowess_bell_shape_kern, create_opensim_storage
from tkinter import *
from tkinter import filedialog


def createTRC_GRF(path, file):
    c3dFileFull = os.path.relpath(file)
    print(c3dFileFull)
    c3dFile = c3dFileFull[c3dFileFull.rfind("\\") + 1:]
    print(c3dFile)

    c3dFileAdapter = osim.C3DFileAdapter()
    c3dFileAdapter.setLocationForForceExpression(osim.C3DFileAdapter.ForceLocation_CenterOfPressure)
    tables = c3dFileAdapter.read(c3dFileFull)

    markersTable = c3dFileAdapter.getMarkersTable(tables)

    rotate_data_table(markersTable, [1, 0, 0], -90)  # rotacao em X
    rotate_data_table(markersTable, [0, 1, 0], -90)  # rotacao em Z

    osim.TRCFileAdapter.write(markersTable, path + c3dFile + '.trc')

    forcesTable = c3dFileAdapter.getForcesTable(tables)
    rotate_data_table(forcesTable, [1, 0, 0], -90)  # rotacao em X
    rotate_data_table(forcesTable, [0, 1, 0], -90)  # rotacao em Z

    if (len(forcesTable.getColumnLabels()) != 0):
        # conversion of unit (f -> N, p -> mm, tau -> Nmm)
        mm_to_m(forcesTable, 'p1')
        mm_to_m(forcesTable, 'p2')
        mm_to_m(forcesTable, 'm1')
        mm_to_m(forcesTable, 'm2')

        stoAdapter = osim.STOFileAdapter()
        # Flatten forces data.
        forcesFlat = forcesTable.flatten()

        t = forcesFlat.getIndependentColumn()
        labels = forcesFlat.getColumnLabels()
        list_mat = []

        # interpolate and fit splines to smooth the data
        for label in labels:
            f = forcesFlat.getDependentColumn(label)
            # list_mat.append(lowess_bell_shape_kern(t, f, output_dir=path))
            for i in range(0, f.size()):
                if np.isnan(f[i]):
                    # print('ACHEI')
                    f[i] = 0.0
            list_mat.append(f.to_numpy())

        # construct the matrix of the forces (forces, moments, torques / right and left)
        # (type opensim.Matrix)
        forces_task_np = np.array(list_mat)
        if 'p2' in forcesTable.getColumnLabels():
            numMat = 18
            labels_list = ['1_ground_force_vx', '1_ground_force_vy', '1_ground_force_vz',
                           '1_ground_force_px', '1_ground_force_py', '1_ground_force_pz',
                           '1_ground_torque_x', '1_ground_torque_y', '1_ground_torque_z',
                           '2_ground_force_vx', '2_ground_force_vy', '2_ground_force_vz',
                           '2_ground_force_px', '2_ground_force_py', '2_ground_force_pz',
                           '2_ground_torque_x', '2_ground_torque_y', '2_ground_torque_z']
        else:
            numMat = 9
            labels_list = ['1_ground_force_vx', '1_ground_force_vy', '1_ground_force_vz',
                           '1_ground_force_px', '1_ground_force_py', '1_ground_force_pz',
                           '1_ground_torque_x', '1_ground_torque_y', '1_ground_torque_z']
        forces_task_mat = osim.Matrix(len(t), numMat)

        for j in range(0, numMat):
            for i in range(0, len(t)):
                forces_task_mat.set(i, j, forces_task_np[j, i])

        # export forces

        force_sto = create_opensim_storage(t, forces_task_mat, labels_list)
        force_sto.setName('GRF')
        # force_sto.printResult(force_sto, c3dFile+'_grf', path, 0.001, '.mot')
        force_sto.lowpassFIR(4, 6)
        force_sto.printResult(force_sto, c3dFile[:-4] + '_grf', path, 0.001, '.mot')


def conversaoC3D():
    root = Tk()

    options = {}
    options['title'] = "SELECIONE PASTA COM ARQUIVOS C3D"

    diretorio = filedialog.askdirectory(**options)
    print('LENDO DIRETORIO = ' + diretorio)
    #path = os.path.basename(diretorio)
    path = diretorio + '/'

    listaFiles = []
    for file in os.listdir(path):
        if file.endswith(".c3d"):
            listaFiles.append(path + file)

    for file in listaFiles:
        print("Processando --- " + file)
        createTRC_GRF(path, file)


def main():
    conversaoC3D()


if __name__ == '__main__':
    main()

