import copy
import working_scad

def main(**kwargs):
    kwargs["run_oomp_populate"] = True

    kwargs["run_oomp"] = True

    kwargs["run_action"] = False
    #kwargs["run_action"] = False

    kwargs["run_scad"] = True
    kwargs["run_solidcraft"] = False

    kwargs["generate_stl"] = True
    # Consume YAML only after OOMP has finished writing every part.
    kwargs.setdefault("wait_for_completion", True)

    import working
    working.run(**kwargs)

if __name__ == '__main__':
    kwargs = {}
    main(**kwargs)
